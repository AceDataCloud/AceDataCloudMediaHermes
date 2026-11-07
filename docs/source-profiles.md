# Single-service Git source profiles / 单服务源码变体

The official catalog remains one `acedatacloud-media` product line, with per-service
toolset selection. A custom Git source install can instead register only one
service's two tools. The first supported profiles are Suno, Seedance, Happy Horse,
GPT Image and Nano Banana. No extra official listings are proposed.

This repository is the only maintained transport/contract source. From an exact
canonical commit, run:

```sh
python3 scripts/export_service.py --service suno --output /path/to/SunoHermes
python3 scripts/export_service.py --service suno --output /path/to/SunoHermes --check
```

The exporter preserves the candidate's old spec/tests/live evidence in `history/`,
copies the hardened `client.py` exactly, selects one `services/*.json` contract,
and changes only public identities and source metadata. Generate/retrieve paths,
request schemas/defaults, paid behavior and no-retry/task recovery stay canonical.
The original candidate had no unique request capability beyond this contract;
its minimal Git installation route is retained.

Generated `source-lock.json` records the immutable source commit, transport hash,
operation-contract hash, identity map and generated file hashes. Consumer CI
checks out that exact source and compares the exporter output, then runs normal
unittest discovery and official Hermes validation. Runtime fixes belong here,
followed by deliberate regeneration; consumer transport is not edited by hand.

Names use `acedatacloud_single_` and `acedatacloud-single-` to avoid overwriting
existing official media tools. Nano's native image provider is separately named
`acedatacloud-single-nano-banana`; its recovery tool and Applications signup URL
follow the variant. Tests cover each variant alone and co-installed with the
released media 2.0.2 in both `in_process` and `host` isolation. Enable one integration
per service to prevent the model from intentionally issuing duplicate calls.

These are source merges, not PyPI uploads, official catalog admission or default
preinstallation. Tests make no paid requests: transport calls are mocked and
real-host dispatch uses invalid parameters. Screenshots retain their original
2026-10-18 dates. Current GUI, generation, billing and conversion remain separate.

中文：官方仍为一条媒体目录入口；单服务 Git 路线保留，只注册所选服务两个工具。
单一源码由本仓生成器维护，CI 按固定 commit 重新生成检查，不能手写维护多个
transport 副本。历史候选 spec/测试/实测证据移入 history 保留。收费行为、无审批
提示、不自动重试、同 ID 恢复、Applications 专用 Token、四字段 UTM 和双语图文
均在生成文档中明确；不把源码合并写成官方收录、默认内置或收费 E2E。
