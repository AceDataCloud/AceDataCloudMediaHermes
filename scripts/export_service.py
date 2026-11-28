"""Build source-only single-service Git plugins from this canonical source.

Generated transports and contracts are never hand-maintained downstream. A locked
canonical checkout regenerates and checks every managed file in consumer CI.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/AceDataCloud/AceDataCloudMediaHermes'
HOST = '3b421578588243f920886e6fe79a6faa87ea026e'
HOST_VERSION = '0.23.1'
SERVICES = {
    'acemusic': ('ACE Music', 'ACEMusicHermes'),
    'suno': ('Suno', 'SunoHermes'),
    'seedance': ('Seedance', 'SeedanceHermes'),
    'happyhorse': ('Happy Horse', 'HappyHorseHermes'),
    'gpt-image': ('GPT Image', 'GPTImageHermes'),
    'nano-banana': ('Nano Banana', 'NanoBananaHermes'),
    'face': ('Face Analysis', 'FaceHermes'),
    'fish': ('Fish Audio', 'FishAudioHermes'),
    'flux': ('FLUX', 'FluxHermes'),
    'google-search': ('Google Search', 'GoogleSearchHermes'),
    'grok': ('Grok Video', 'GrokHermes'),
    'hailuo': ('Hailuo', 'HailuoHermes'),
    'luma': ('Luma Dream Machine', 'LumaHermes'),
    'kling': ('Kling', 'KlingHermes'),
    'midjourney': ('Midjourney', 'MidjourneyHermes'),
    'minimax': ('MiniMax H3', 'MiniMaxHermes'),
    'qwen-image': ('Qwen Image', 'QwenImageHermes'),
    'seedream': ('Seedream', 'SeedreamHermes'),
    'veo': ('Veo', 'VeoHermes'),
    'wan': ('Wan', 'WanHermes'),
}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def build(service, source_ref):
    title, repository = SERVICES[service]
    source_spec = json.loads((ROOT / 'services' / (service + '.json')).read_text())
    spec = copy.deepcopy(source_spec)
    prefix = 'acedatacloud_single_' + service.replace('-', '_')
    old_prefix = spec['tool_prefix']
    spec.update(tool_prefix=prefix, toolset='acedatacloud-single-' + service,
                generate_name=spec['generate_name'].replace(old_prefix, prefix),
                tools=[name.replace(old_prefix, prefix) for name in spec['tools']],
                repo=repository)
    plugin_name = 'acedatacloud-' + service
    utm = 'utm_source=hermes&utm_medium=referral&utm_campaign=evergreen'
    application = 'https://platform.acedata.cloud/console/applications?' + utm
    pricing = 'https://platform.acedata.cloud/models?' + utm
    manifest = {
        'name': plugin_name, 'version': '1.0.0', 'author': 'AceDataCloud',
        'description': f'{title} by Ace Data Cloud: source-only single-service Git plugin. '
                       'The primary operation spends paid Credits without a Hermes approval prompt; model options can increase cost. '
                       'Prompts/reference URLs go to api.acedata.cloud. Never automatically retry a paid request.',
        'requires_hermes': '>=' + HOST_VERSION, 'provides_tools': spec['tools'],
        'requires_env': ['ACEDATACLOUD_API_KEY'],
    }
    image = (ROOT / 'image_provider.py').read_text()
    if service == 'nano-banana':
        image = image.replace("'acedatacloud-nano-banana'", "'acedatacloud-single-nano-banana'")
        image = image.replace("'Ace Data Cloud Nano Banana'", "'Ace Data Cloud Nano Banana (single service)'")
        image = image.replace('acedatacloud_nano_banana_task', prefix + '_task')
        image = image.replace("'https://platform.acedata.cloud'", repr(application))
    files = {
        '__init__.py': (ROOT / '__init__.py').read_bytes(),
        'client.py': (ROOT / 'client.py').read_bytes(),
        'image_provider.py': image.encode(),
        'services/' + service + '.json': encoded(spec),
        'plugin.yaml': encoded(manifest),
        'tests/test_contracts.py': (ROOT / 'tests/test_contracts.py').read_bytes(),
        'tests/test_registration.py': (ROOT / 'tests/test_registration.py').read_bytes(),
        'tests/test_source_profile.py': (ROOT / 'profiles/test_source_profile.py').read_bytes(),
        'scripts/check_runtime.py': (ROOT / 'profiles/check_source_runtime.py').read_bytes(),
        'LICENSE': (ROOT / 'LICENSE').read_bytes(),
    }
    workflow = '''name: Validate single-service Hermes source
on: [push, pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          repository: AceDataCloud/AceDataCloudMediaHermes
          ref: SOURCE_REF
          path: .canonical-source
      - name: Check generated source against immutable canonical commit
        run: |
          mv .canonical-source "$RUNNER_TEMP/canonical-media"
          python3 "$RUNNER_TEMP/canonical-media/scripts/export_service.py" --service SERVICE --output . --check
      - name: Unit contracts (mocked network only)
        run: python3 -m unittest discover -s tests -v
      - uses: NousResearch/hermes-agent/.github/actions/plugin-validate@HOST_REF
        with:
          path: ${{ github.workspace }}
          hermes-ref: 'HOST_REF'
      - name: Normal Git install, minimal tools and co-installation (two isolation modes)
        env:
          PLUGIN_SOURCE_REF: ${{ github.event.pull_request.head.sha || github.sha }}
        shell: bash
        run: |
          set -euo pipefail
          hermes_source=("$RUNNER_TEMP"/hermes-plugin-validator.*)
          export HERMES_SOURCE="${hermes_source[0]}"
          export PYTHONPATH="$HERMES_SOURCE"
          "$HERMES_SOURCE/.build/validator/bin/python" -m unittest discover -s tests -v
          "$HERMES_SOURCE/.build/validator/bin/python" scripts/check_runtime.py
'''.replace('ref: SOURCE_REF', 'ref: ' + source_ref).replace('SERVICE', service).replace('HOST_REF', HOST)
    # Keep the canonical checkout out of normal plugin discovery and packaging.
    files['.github/workflows/validate.yml'] = workflow.encode()
    has_task = bool(spec.get('task_path'))
    tool_count = len(spec['tools'])
    task_en = (f'- Query an existing task: `{prefix}_task`, with `task_id` and optional '
               '`wait_seconds` (0–60). Pending/preview media is not final success.'
               if has_task else
               '- This service returns a synchronous result. There is no task-query tool or task polling.')
    task_zh = (f'已有任务查询工具为 `{prefix}_task`，传入 `task_id` 及可选 '
               '`wait_seconds`（0–60）；pending/预览媒体不视为终态成功。'
               if has_task else
               '此服务同步返回结果，只有一个收费操作工具，没有任务查询工具或轮询。')
    recover_en = ('Recover pending work with the same task ID; task lookup never creates a generation.'
                  if has_task else
                  'A synchronous search or analysis is also paid; do not assume an automatic retry is free.')
    recover_zh = ('使用同一任务 ID 恢复 pending 任务，查询不会新建生成。'
                  if has_task else
                  '同步搜索和分析同样收费，不能将自动重试视为免费，也不存在任务查询能力。')
    screenshot_service = service if service in {'suno', 'seedance', 'happyhorse', 'gpt-image', 'nano-banana'} else 'gpt-image'
    screenshot_file = 'happy-horse' if screenshot_service == 'happyhorse' else screenshot_service
    screenshot = f'{REPO}/raw/8eaebfb86152d754061375de881548bfa096dd2d/assets/tutorial/hermes-{screenshot_file}-search.jpg'
    native = ('The native image backend is `acedatacloud-single-nano-banana`; the official media backend '
              'remains `acedatacloud-nano-banana`. Select only the backend you intend to use.'
              if service == 'nano-banana' else 'This variant registers no native image backend.')
    prior_candidate = service not in {'acemusic', 'hailuo', 'luma'}
    legacy_note = ('- To migrate the previous candidate, update saved tool names and retain original task IDs.'
                   if prior_candidate else '')
    history_en = 'Earlier candidate material is preserved in `history/`.' if prior_candidate else ''
    history_zh = '原候选资料保存在 `history/`。' if prior_candidate else ''
    requires_new_media = service in {'hailuo', 'luma'}
    catalog_en = ('Check `hermes plugins info acedatacloud-media` first. The official catalog must offer '
                  '2.2.0 or later to include this toolset. Until then use the Git install above.'
                  if requires_new_media else 'Install `acedatacloud-media` and enable the desired toolset.')
    catalog_zh = ('先用 `hermes plugins info acedatacloud-media` 检查目录版本。此工具集需要 2.2.0 或更高版本。'
                  '目录尚未更新时，请使用上面的 Git 安装方式。'
                  if requires_new_media else '安装 `acedatacloud-media` 并选择本服务工具集。')
    migration_zh = ('旧候选 `acedata_` 名称已移除，无别名；原服务如果有任务查询工具，旧任务 ID 可继续查询。'
                    if prior_candidate else '')
    readme = f'''# {title} by Ace Data Cloud for Hermes

[简体中文](readme/README_zh_Hans.md)

{spec['description']}

A source-only single-service Git installation: **only {title}'s {tool_count} tool(s)**
are registered. Maintained by Ace Data Cloud; no affiliation with the service maker
is implied. Requires Hermes **{HOST_VERSION}+**. The canonical **Ace Data Cloud Media** source includes the same service profile.

## Install this service from Git

```sh
hermes plugins install https://github.com/AceDataCloud/{repository} --enable
hermes config set ACEDATACLOUD_API_KEY '<your-application-api-key>'
hermes tools enable {spec['toolset']}
hermes tools list
```

This installs the repository's current default branch. For a reproducible install
or rollback, add `--ref <40-character-source-SHA>` using the merged commit in its
history, then start a new session. CI tests normal Git installation at the exact
source SHA. No PyPI package, default preinstallation or independent official
catalog entry is claimed.

For the reviewed official distribution, open
[Ace Data Cloud Media](https://hermes-agent.nousresearch.com/docs/plugins/acedatacloud-media)
for the package description. {catalog_en}
The [one-product-line rule](https://github.com/NousResearch/hermes-agent/pull/135239#issuecomment-6096145033)
continues to apply. This repository's service name and tool names identify its
source Git route; do not use a bare service name expecting a separate catalog entry.

## Application API key and spending

1. Open [Ace Data Cloud → Applications]({application}); sign in or register.
2. Initialize **General application** if needed, or use a dedicated application
   with access to this service. Open **Keys / Manage Keys → Create** and name a
   separately revocable key for Hermes.
3. Review expiration, usage limits and Allowed APIs. Copy the raw token without
   `Bearer ` into the active Hermes profile. A `platform-...` management token
   cannot replace an application API key. Keep it out of prompts and Git.
4. Check [current pricing and balance]({pricing}) before any call. Trial allowance
   is whatever the account currently displays; installing is not free usage.

![Applications API key guide, sourced from existing Ace documentation](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

**The primary operation spends paid Credits without a Hermes approval prompt.** The
model may choose costly model/resolution/count options where the service supports
them. Prompts and reference URLs go to **api.acedata.cloud**. Enabling tools permits
their use with your key; schema constraints are not a spending budget. There is
**no automatic retry** of a paid request. On timeout or unknown delivery, check
request history before taking another action. {recover_en}

## Tools, migration and co-installation

- Primary operation: `{spec['generate_name']}`.
{task_en}
{legacy_note}
- Source variants use `acedatacloud_single_` tool names and
  `acedatacloud-single-` toolsets, distinct from official media registrations.
  If both are installed, enable only one integration per service to avoid
  accidental duplicate paid calls. No profile preferences change automatically.
- {native}

## Canonical source and validation boundary

Generated by [{REPO}]({REPO}) at `{source_ref}` using
`scripts/export_service.py --service {service}`. Transport and operation schemas
have one maintained source; `source-lock.json` records exact file hashes and
identity transformations. Consumer CI checks regenerated files against that
immutable checkout. Submit runtime/schema fixes to the canonical repository,
then deliberately regenerate; do not hand-edit downstream transport copies.

Normal CI runs unittest discovery, the official Hermes {HOST_VERSION} validator,
normal exact-SHA Git installation, and fresh in-process/host profiles both alone
and alongside official media 2.0.2. Valid transport requests are mocked; host
dispatch uses invalid inputs. Green source CI does not prove a new paid request,
unique billing, current GUI interaction, default installation or catalog admission.
{history_en}

![Historical real official media catalog screenshot, captured 2026-10-18]({screenshot})

Historical **2026-10-18** screenshot of the official media **2.0.1** entry.
It illustrates that shared catalog entry, not a search for this service, this
source variant, a new paid result or a current GUI test.
'''
    chinese = f'''# {title} by Ace Data Cloud：Hermes 单服务 Git 安装

[English](../README.md)

本源码变体只注册 **{title} 的 {tool_count} 个工具**，由 Ace Data Cloud 维护，不表示与服务品牌方有隶属关系。需要 Hermes **{HOST_VERSION}+**。官方目录仍只有 `acedatacloud-media` 一条媒体产品线入口，源码合并不表示独立官方收录或默认预装。

## 安装与应用 Token

```sh
hermes plugins install https://github.com/AceDataCloud/{repository} --enable
hermes config set ACEDATACLOUD_API_KEY '<应用API密钥>'
hermes tools enable {spec['toolset']}
hermes tools list
```

默认安装仓库当前默认分支；如需固定版本或回滚，增加 `--ref <40位源码SHA>`，使用本仓已合并源码 commit，启用后开始新会话。CI 验证普通 Git URL 加精确 SHA 安装。要使用官方入口，请打开[官方媒体页面](https://hermes-agent.nousresearch.com/docs/plugins/acedatacloud-media)。{catalog_zh}未发布 PyPI 新项目，也未承诺本变体另获官方 listing。

1. 打开 [Ace Data Cloud → Applications]({application})，登录或注册。
2. 如未初始化，先初始化“通用应用”；也可选择具有本服务权限的专用应用。在“密钥 / 管理密钥 → 创建”中新建可单独撤销的 Hermes 密钥。
3. 检查到期时间、使用量限制和允许 API。复制不含 `Bearer ` 的原始 Token 到当前 Hermes profile；`platform-...` 管理 Token 不能替代应用 API Key。不要写进提示词或 Git。
4. 调用前检查[当前价格与余额]({pricing})。试用额度以账户实际显示为准，安装成功不表示免费使用。

![应用密钥获取指引（英文界面原图），来源于已有 Ace 文档](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

**主操作立即消耗 Credits，不会出现 Hermes 审批提示。** 模型可以选择服务支持的高价模型、分辨率或数量选项。提示词和参考 URL 发送至 `api.acedata.cloud`。启用即允许模型使用密钥调用，schema 限制不等于预算。收费请求**不自动重试**；超时或送达未知时先查请求历史。{recover_zh}

## 工具与共装

主工具：`{spec['generate_name']}`。{task_zh}
{migration_zh}

本变体使用 `acedatacloud_single_` 名称及 `{spec['toolset']}` 工具集，与官方媒体包的名称分开，避免共装覆盖。两者同时安装时同一服务只启用一种，避免模型重复收费调用；插件不自动改 profile 的其他选择。{'Nano 原生图像后端为 `acedatacloud-single-nano-banana`，与官方包 `acedatacloud-nano-banana` 分开，按需选择一个。' if service == 'nano-banana' else '此服务不注册原生图像后端。'}

## 单一源码与验收边界

由 [canonical 媒体源码]({REPO}) 的 `{source_ref}` 统一生成。`source-lock.json` 固定 transport/schema 的来源、哈希和名称映射，CI 用同一 commit 重新生成比较。runtime/schema 修复先交唯一源，再生成消费仓，不手写维护多套底座。{history_zh}

CI 包括 unittest 正常发现、Hermes {HOST_VERSION} 官方校验、按精确 SHA 正常 Git 安装、两种隔离模式的单独/共装注册和无效输入 dispatch。mock/宿主兼容不等于新收费请求、唯一账单、当前 GUI、默认预装或官方收录。

![2026-10-18 真实官方媒体目录历史截图]({screenshot})

截图为 **2026-10-18** 官方媒体 **2.0.1** 历史页面，只展示共同媒体目录项，不是本服务搜索、本源码变体、新收费结果或当前 GUI 验收。
'''
    service_icons = {'hailuo': 'https://cdn.acedata.cloud/0qg4gp.png',
                     'luma': 'https://cdn.acedata.cloud/ahjfwi.png'}
    if service in service_icons:
        icon = f'<img src="{service_icons[service]}" width="64" height="64" alt="{title}">'
        readme = readme.replace('\n\n', f'\n\n{icon}\n\n', 1)
        chinese = chinese.replace('\n\n', f'\n\n{icon}\n\n', 1)
    files.update({'README.md': readme.encode(), 'readme/README_zh_Hans.md': chinese.encode()})
    provenance = {
        'canonical_repository': REPO, 'canonical_commit': source_ref,
        'generator': 'scripts/export_service.py', 'service': service,
        'consumer_repository': 'https://github.com/AceDataCloud/' + repository,
        'canonical_contract': 'services/' + service + '.json',
        'identity_map': {'tool_prefix': [old_prefix, prefix],
                         'toolset': [source_spec['toolset'], spec['toolset']],
                         'native_image_provider': ['acedatacloud-nano-banana', 'acedatacloud-single-nano-banana'] if service == 'nano-banana' else None},
        'transport_sha256': digest(files['client.py']),
        'canonical_operation_sha256': digest(encoded({k: v for k, v in source_spec.items() if k not in {'repo', 'tool_prefix', 'toolset', 'tools', 'generate_name'}})),
        'generated_files': {path: digest(data) for path, data in files.items()},
    }
    files['source-lock.json'] = encoded(provenance)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', choices=SERVICES, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    ref = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    files = build(args.service, ref)
    stale = ['spec.json', 'tests/test_plugin.py']
    if args.check:
        changed = [p for p, data in files.items() if not (args.output / p).is_file() or (args.output / p).read_bytes() != data]
        changed += [p for p in stale if (args.output / p).exists()]
        services = list((args.output / 'services').glob('*.json'))
        if len(services) != 1:
            changed.append('services/: expected exactly one contract')
        if changed:
            raise SystemExit('Generated source differs: ' + ', '.join(changed))
        print('Canonical generated source verified:', args.service, ref)
        return
    # Preserve the unpublished candidate's distinct provenance before replacing it.
    for path in stale + ['tests/live-evidence.json']:
        old = args.output / path
        if old.exists():
            history = args.output / 'history/legacy-candidate' / path
            history.parent.mkdir(parents=True, exist_ok=True)
            if not history.exists():
                history.write_bytes(old.read_bytes())
            old.unlink()
    for path, data in files.items():
        target = args.output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print('Generated:', args.service, ref, len(files), 'files')


if __name__ == '__main__':
    main()
