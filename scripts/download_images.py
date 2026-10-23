"""Download only the references already present in data/references.json."""
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,time,urllib.request,urllib.error
from pathlib import Path
from PIL import Image

def run_git(repo,*args):
    r=subprocess.run(['git','-C',str(repo),*args],text=True,capture_output=True,encoding='utf8',errors='replace')
    if r.returncode:raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--progress-file');p.add_argument('--publish',action='store_true');p.add_argument('--workers',type=int,default=8);a=p.parse_args()
    repo=Path(a.repo).resolve();manifest=repo/'data/references.json';data=json.loads(manifest.read_text(encoding='utf8'));records=data['records'];fallback_file=repo/'data/download_sources.json';fallbacks=json.loads(fallback_file.read_text(encoding='utf8')) if fallback_file.exists() else {}
    done=0;failed=0;total_bytes=0;staged=[];last_sha='';last_pushed=0;start=time.time();errors=[]
    def save():
        temp=manifest.with_suffix('.json.part');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');os.replace(temp,manifest)
    def progress(stage):
        state={'total':len(records),'downloaded':done,'failed':failed,'bytes':total_bytes,'elapsed_seconds':round(time.time()-start),'stage':stage,'last_remote_sha':last_sha,'last_pushed_images':last_pushed}
        (repo/'.download-state.json').write_text(json.dumps(state,indent=2),encoding='utf8')
        if a.progress_file:
            Path(a.progress_file).write_text('# Progresso: biblioteca de UI no GitHub\n\n'
                +f'- Etapa: **{stage}**\n- Base existente: **{len(records):,} referencias**, 20 macroareas.\n- Imagens baixadas e validadas: **{done:,}/{len(records):,}**.\n- Downloads com falha: **{failed}**.\n- Volume baixado: **{total_bytes/1e9:.2f} GB**.\n- Imagens no ultimo push verificado: **{last_pushed:,}**.\n- Ultimo commit remoto: `{last_sha or "a21f9dd"}`.\n'
                +'- Repositorio privado: https://github.com/C-Icaro/ui-references-pinterest\n- Planilha: https://docs.google.com/spreadsheets/d/1ZWwUpsseGXfKOrHad4wzGtBz8UV0rlT6DKb1f8c8y-c/edit\n- Checkout: D:/Codex/ui-references-pinterest\n\n'
                +'Usando somente a base ja coletada. Cada imagem preserva o arquivo disponivel na fonte, sem redimensionamento.\n',encoding='utf8')
        print(json.dumps(state),flush=True)
    def publish():
        nonlocal staged,last_sha,last_pushed
        if not a.publish:return
        if run_git(repo,'config','--get','user.name')!='Carlos Paiva' or run_git(repo,'config','--get','user.email')!='carlosicaro13@gmail.com':raise RuntimeError('Unexpected Git author identity')
        if run_git(repo,'remote','get-url','origin')!='https://github.com/C-Icaro/ui-references-pinterest.git':raise RuntimeError('Unexpected Git destination')
        progress('Enviando checkpoint ao GitHub')
        save();spec=repo/'.git/image-pathspec';spec.write_text('\n'.join(staged)+'\n',encoding='utf8')
        if staged:run_git(repo,'add','--pathspec-from-file=.git/image-pathspec')
        run_git(repo,'add','data','scripts','requirements.txt','README.md')
        if run_git(repo,'diff','--cached','--name-only'):
            run_git(repo,'commit','-m',f'feat: preserva {done} imagens da base existente')
            run_git(repo,'push','origin','main')
        last_sha=run_git(repo,'rev-parse','HEAD');remote=run_git(repo,'ls-remote','origin','refs/heads/main').split()[0]
        if last_sha!=remote:raise RuntimeError('Remote SHA verification failed')
        last_pushed=done;staged=[];progress('Download das imagens existentes')
    def fetch(row):
        existing=repo/row['local_path']
        if row.get('download_status')=='downloaded' and existing.exists():
            return {'download_status':'downloaded','image_sha256':row['image_sha256'],'image_bytes':existing.stat().st_size,'local_path':row['local_path'],'download_url':row.get('download_url',row['image_url']),'image_width':row.get('image_width'),'image_height':row.get('image_height')}
        urls=list(dict.fromkeys([row['image_url'],*fallbacks.get(row['image_signature'],[])]));failure=''
        for url in urls:
            for attempt in range(2):
                part=None
                try:
                    if shutil.disk_usage(repo).free<2*1024**3:raise RuntimeError('Less than 2 GiB free disk space')
                    existing.parent.mkdir(parents=True,exist_ok=True);part=existing.with_suffix(existing.suffix+'.part');sha=hashlib.sha256();size=0
                    with urllib.request.urlopen(url,timeout=40) as response,part.open('wb') as f:
                        if not response.headers.get('Content-Type','').startswith('image/'):raise ValueError('Source did not return an image')
                        while True:
                            chunk=response.read(256*1024)
                            if not chunk:break
                            size+=len(chunk)
                            if size>95*1024**2:raise ValueError('Image exceeds 95 MiB Git blob budget')
                            sha.update(chunk);f.write(chunk)
                    with Image.open(part) as image:
                        width,height=image.size;fmt=image.format;image.verify()
                    ext={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp','GIF':'.gif','AVIF':'.avif'}.get(fmt,existing.suffix)
                    final=existing.with_suffix(ext);os.replace(part,final)
                    return {'download_status':'downloaded','image_sha256':sha.hexdigest(),'image_bytes':size,'local_path':final.relative_to(repo).as_posix(),'download_url':url,'image_width':width,'image_height':height}
                except Exception as e:
                    failure=type(e).__name__+': '+str(e)
                    if part and part.exists():part.unlink()
                    if isinstance(e,urllib.error.HTTPError) and e.code in [401,403,404]:break
                    if attempt==0:time.sleep(1)
        return {'download_status':'failed','download_error':failure}
    progress('Download das imagens existentes')
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(fetch,r):r for r in records}
        for f in concurrent.futures.as_completed(futures):
            row=futures[f];result=f.result();row.update(result)
            if result['download_status']=='downloaded':done+=1;total_bytes+=result['image_bytes'];staged.append(result['local_path'])
            else:failed+=1;errors.append({'id':row['id'],'url':row['image_url'],'error':row['download_error']})
            count=done+failed
            if count%25==0:progress('Download das imagens existentes')
            if count%100==0:save()
            if count%1000==0:publish()
    save()
    audit={'total':len(records),'downloaded':done,'failed':failed,'bytes':total_bytes,'unique_image_signatures':len({r['image_signature'] for r in records}),'errors':errors}
    (repo/'data/download_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    publish();progress('Concluido' if failed==0 else 'Download encerrado com falhas a revisar')
    if failed:raise SystemExit(2)
if __name__=='__main__':main()
