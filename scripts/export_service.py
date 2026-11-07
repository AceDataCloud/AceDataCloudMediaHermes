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
HOST = '2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19'
SERVICES = {
    'suno': ('Suno', 'SunoHermes'),
    'seedance': ('Seedance', 'SeedanceHermes'),
    'happyhorse': ('Happy Horse', 'HappyHorseHermes'),
    'gpt-image': ('GPT Image', 'GPTImageHermes'),
    'nano-banana': ('Nano Banana', 'NanoBananaHermes'),
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
    utm = f'utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content={repository.lower()}_readme'
    application = 'https://platform.acedata.cloud/console/applications?' + utm + '_api_key'
    pricing = 'https://platform.acedata.cloud/models?' + utm + '_pricing'
    manifest = {
        'name': plugin_name, 'version': '1.0.0', 'author': 'AceDataCloud',
        'description': f'{title} by Ace Data Cloud: source-only single-service Git plugin. '
                       'Calls spend paid Credits without a Hermes approval prompt; model options can increase cost. '
                       'Prompts/reference URLs go to api.acedata.cloud. Never automatically resubmit generation.',
        'requires_hermes': '>=0.23.0', 'provides_tools': spec['tools'],
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
    screenshot = f'{REPO}/raw/8eaebfb86152d754061375de881548bfa096dd2d/assets/tutorial/hermes-{service if service != "happyhorse" else "happy-horse"}-search.jpg'
    native = ('The native image backend is `acedatacloud-single-nano-banana`; the official media backend '
              'remains `acedatacloud-nano-banana`. Select only the backend you intend to use.'
              if service == 'nano-banana' else 'This variant registers no native image backend.')
    readme = f'''# {title} by Ace Data Cloud for Hermes

[简体中文](readme/README_zh_Hans.md)

A source-only single-service Git installation: **only {title}'s two tools** are
registered. Maintained by Ace Data Cloud; no affiliation with the service maker
is implied. Requires Hermes **0.23.0+**. This is an alternative to selecting the
same service in the official **Ace Data Cloud Media** package.

## Install this service from Git

```sh
hermes plugins install https://github.com/AceDataCloud/{repository} --ref <40-character-source-SHA> --enable
hermes config set ACEDATACLOUD_API_KEY '<your-application-api-key>'
hermes tools enable {spec['toolset']}
hermes tools list
```

Use the merged source commit shown in this repository's history, then start a new
session. No PyPI package or independent official catalog entry is claimed.
For the reviewed official distribution, search `{title}` in the
[Hermes catalog](https://hermes-agent.nousresearch.com/docs/plugins) and install
`acedatacloud-media`. Its [one-product-line rule](https://github.com/NousResearch/hermes-agent/pull/135239#issuecomment-6096145033)
continues to apply. Do not install a bare service name expecting this adapter.

## Application API key and spending

1. Open [Ace Data Cloud → Applications]({application}); sign in or register.
2. Initialize **General application** if needed, or use a dedicated application
   with access to this service. Open **Keys / Manage Keys → Create** and name a
   separately revocable key for Hermes.
3. Review expiration, usage limits and Allowed APIs. Copy the raw token without
   `Bearer ` into the active Hermes profile. A `platform-...` management token
   cannot replace an application API key. Keep it out of prompts and Git.
4. Check [current pricing and balance]({pricing}) before any call. Trial allowance
   is whatever the account currently displays; installing is not free generation.

![Applications API key guide, sourced from existing Ace documentation](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

**Every generation spends paid Credits without a Hermes approval prompt.** The
model can select costly model/resolution/count options where supported. Prompts
and reference URLs are sent to **api.acedata.cloud**. Enabling tools permits their
use with your key; schema constraints are not a budget. A generation is submitted
**once, with no automatic retry**. On a timeout or unknown delivery, check request
history and recover the same task ID; do not generate again. Task lookup does not
submit a new generation and does not grant generation permission.

## Tools, migration and co-installation

- Generate: `{spec['generate_name']}`.
- Query an existing task: `{prefix}_task` with `task_id` and optional
  `wait_seconds` (0–60). Pending/preview media is not final success.
- The unmerged candidate's old `acedata_` names are removed, without aliases.
  Update saved prompts/tool selections; existing task IDs remain usable.
- Source variants use `acedatacloud_single_` tool names and
  `acedatacloud-single-` toolsets. They do not overwrite official media tools.
  If both are installed, enable only one integration for the service to avoid
  accidental duplicate generation. No profile preferences are changed automatically.
- {native}

## Canonical source and validation boundary

Generated by [{REPO}]({REPO}) at `{source_ref}` using
`scripts/export_service.py --service {service}`. Transport and operation schemas
have one maintained source; `source-lock.json` records exact file hashes and
identity transformations. Consumer CI checks regenerated files against that
immutable checkout. Submit runtime/schema fixes to the canonical repository,
then deliberately regenerate; do not hand-edit downstream transport copies.

Normal CI runs unittest discovery, the official Hermes 0.23.0 validator, normal
Git installation with an exact source SHA, and fresh in-process/host profiles
both alone and alongside official media 2.0.2. Unit requests are mocked; host
dispatch uses invalid inputs. Green source CI does not prove a new paid task,
unique billing, current GUI interaction, default installation or catalog admission.
Original candidate specs and dated live evidence are preserved in `history/`.

![Historical real official catalog search, captured 2026-10-18]({screenshot})

Historical **2026-10-18** screenshot of the official media **2.0.1** entry;
it is not this source variant, a new generation result or a current GUI test.
'''
    chinese = f'''# {title} by Ace Data Cloud：Hermes 单服务 Git 安装

[English](../README.md)

此源码变体只注册 **{title} 的两个工具**，由 Ace Data Cloud 维护，不表示与服务品牌方有隶属关系。需要 Hermes **0.23.0+**。这是独立 Git 源码安装路线；官方目录仍只有 `acedatacloud-media` 一条媒体产品线入口，不能把本仓源码合并当作独立官方收录或默认预装。

## 安装与应用 Token

```sh
hermes plugins install https://github.com/AceDataCloud/{repository} --ref <40位源码SHA> --enable
hermes config set ACEDATACLOUD_API_KEY '<应用API密钥>'
hermes tools enable {spec['toolset']}
hermes tools list
```

使用本仓已合并源码 commit，启用后开始新会话。要使用官方入口，请在[官方目录](https://hermes-agent.nousresearch.com/docs/plugins)搜索 `{title}` 并安装 `acedatacloud-media`。未发布 PyPI 新项目，也未承诺本变体另获官方 listing。

1. 打开 [Ace Data Cloud → Applications]({application})，登录或注册。
2. 如未初始化，先初始化“通用应用”；也可选择具有本服务权限的专用应用。在“密钥 / 管理密钥 → 创建”中新建可单独撤销的 Hermes 密钥。
3. 检查到期时间、使用量限制和允许 API。复制不含 `Bearer ` 的原始 Token 到当前 Hermes profile；`platform-...` 管理 Token 不能替代生成 API Key。不要写进提示词或 Git。
4. 调用前检查[当前价格与余额]({pricing})。试用额度以账户实际显示为准，安装成功不表示免费生成。

![应用密钥获取指引（英文界面原图），来源于已有 Ace 文档](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

**每次生成立即消耗 Credits，不会出现 Hermes 审批提示。** 模型可以选择服务支持的高价模型、分辨率或数量选项。提示词和参考 URL 发送至 `api.acedata.cloud`。启用即允许模型使用密钥调用，schema 限制不等于预算。生成只提交一次，**不自动重试**；超时或送达未知时查请求历史并使用同一任务 ID 恢复，不能再次生成。查询任务不会新建生成，也不会授予生成权限。

## 工具与共装

生成工具：`{spec['generate_name']}`；任务查询：`{prefix}_task`，传入 `task_id` 和可选 `wait_seconds`（0–60）。pending/预览图不视作终态成功。旧候选 `acedata_` 名称已移除，无别名；旧任务 ID 可继续查询。

本变体使用 `acedatacloud_single_` 名称及 `{spec['toolset']}` 工具集，与官方媒体包的名称分开，避免共装覆盖。两者同时安装时同一服务只启用一种，避免模型重复生成；插件不自动改 profile 的其他选择。{'Nano 原生图像后端为 `acedatacloud-single-nano-banana`，与官方包 `acedatacloud-nano-banana` 分开，按需选择一个。' if service == 'nano-banana' else '此服务不注册原生图像后端。'}

## 单一源码与验收边界

由 [canonical 媒体源码]({REPO}) 的 `{source_ref}` 统一生成。`source-lock.json` 固定 transport/schema 的来源、哈希和名称映射，CI 用同一 commit 重新生成比较。runtime/schema 修复先交唯一源，再生成消费仓，不手写维护多套底座。原候选 spec 和历史实测证据保留在 `history/`。

CI 包括 unittest 正常发现、Hermes 0.23.0 官方校验、按精确 SHA 正常 Git 安装、两种隔离模式的单独/共装注册和无效输入 dispatch。mock/宿主兼容不等于新收费任务、唯一账单、当前 GUI、默认预装或官方收录。

![2026-10-18 真实官方目录历史搜索截图]({screenshot})

截图为 **2026-10-18** 官方媒体 **2.0.1** 历史页面，不是此源码变体、新生成结果或当前 GUI 验收。
'''
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
