"""Ephemeral exact-release Git installation evidence; no catalog injection or paid calls."""
from pathlib import Path
import os,sys,json,subprocess,tempfile
from ruamel.yaml import YAML
source=Path(os.environ['HERMES_SOURCE']).resolve()
host=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
assert host==os.environ['HERMES_EXPECTED_SHA']
pins={'acedatacloud':('AceDataCloudModelProviderHermes','568763ee21fe081562bb9bcd91e7323f8f81d6ff','1.0.2'),'acedatacloud-media':('AceDataCloudMediaHermes','8eaebfb86152d754061375de881548bfa096dd2d','2.0.2')}
for mode in ['in_process','host']:
 with tempfile.TemporaryDirectory(prefix='hermes-exact-released-') as tmp:
  home=Path(tmp)
  env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','LANG','TMPDIR','HERMES_RUNTIME_DIR','SSL_CERT_FILE','SSL_CERT_DIR','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY'}}
  env.update(HERMES_HOME=str(home),PYTHONPATH=str(source),HERMES_PYTHON=sys.executable,COLUMNS='180')
  def run(*args,extra=None):
   p=subprocess.run([sys.executable,*args],cwd=home,env={**env,**(extra or {})},capture_output=True,text=True,timeout=300)
   print(p.stdout,end='',flush=True)
   if p.stderr:print(p.stderr,file=sys.stderr,end='',flush=True)
   p.check_returncode()
   return p.stdout
  installed={}
  for name,(repo,sha,version) in pins.items():
   run('-m','hermes_cli.main','plugins','install','https://github.com/AceDataCloud/'+repo,'--ref',sha,'--enable')
   folder=home/'plugins'/name
   got=subprocess.check_output(['git','rev-parse','HEAD'],cwd=folder,text=True).strip();assert got==sha
   yaml=YAML(typ='safe');manifest=yaml.load((folder/'plugin.yaml').read_text());assert manifest['version']==version
   readme=(folder/'README.md').read_text();chinese=(folder/'readme/README_zh_Hans.md').read_text()
   assert 'readme/README_zh_Hans.md' in readme and '未合并模型PR' not in chinese and '仍在源PR#5中' not in chinese
   installed[name]={'sha':sha,'version':version,'chinese':True,'source':'normal Git URL --ref; not yet official catalog pin'}
  yaml=YAML();p=home/'config.yaml';cfg=yaml.load(p.read_text()) or {};cfg['plugins']['isolation']=mode
  with p.open('w') as f:yaml.dump(cfg,f)
  media=home/'plugins/acedatacloud-media'
  for slug in ['suno','seedance','happyhorse','gpt-image','nano-banana']:
   assert (media/'docs'/f'{slug}.md').is_file() and (media/'docs/zh-CN'/f'{slug}.md').is_file()
  run(str(media/'scripts/check_runtime.py'),'--child',mode)
  run('-c',"""
from providers import get_provider_profile
from hermes_cli.runtime_provider import resolve_runtime_provider
from hermes_cli.models import list_available_providers
from urllib.parse import urlsplit,parse_qs
p=get_provider_profile('acedatacloud');assert p is not None
assert parse_qs(urlsplit(p.signup_url).query)=={'utm_source':['opensource'],'utm_medium':['referral'],'utm_campaign':['evergreen'],'utm_content':['hermes_model_picker_api_key']}
r=resolve_runtime_provider(requested='acedatacloud',target_model='gpt-4.1-mini');assert r['api_mode']=='chat_completions' and r['base_url']=='https://api.acedata.cloud/openai'
row=next(r for r in list_available_providers() if r['id']=='acedatacloud');assert row['label']=='Ace Data Cloud' and row['authenticated']
""",extra={'ACEDATACLOUD_API_KEY':'synthetic-no-api-call'})
  print(json.dumps({'released_git_install':'passed','host_sha':host,'mode':mode,'installed':installed,'five_en_zh_guides':True,'model_native_signup_4utm':True,'paid_calls':0}),flush=True)
