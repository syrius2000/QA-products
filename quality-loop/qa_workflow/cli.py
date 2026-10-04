"""平易な次操作を返すCLI。内部JSON入力はSkillが組み立てる。"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .store import QAError
from . import gitops
from .workflow import Workflow
from .legacy import read_legacy


def parser():
    p=argparse.ArgumentParser(description="QA依頼→結果確認→承認後の修正→再QAを案内します")
    p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--json',action='store_true',help='Skill内部向けJSON出力')
    sub=p.add_subparsers(dest='operation',required=True)
    sub.add_parser('preflight',help='Git状態を読み取り専用で確認。変更しない')
    a=sub.add_parser('prepare',help='依頼を準備。commit・pushはしない')
    a.add_argument('--purpose',required=True);a.add_argument('--criterion',action='append',required=True)
    a.add_argument('--target',action='append',required=True);a.add_argument('--implementer',required=True);a.add_argument('--author',required=True)
    a.add_argument('--audience',choices=['local','cloud'],default='cloud');a.add_argument('--assumptions',default='未指定')
    a.add_argument('--baseline');a.add_argument('--reviewed');a.add_argument('--repository');a.add_argument('--exclude',action='append',default=[],metavar='PATH=理由');a.add_argument('--required-test',action='append',default=[]);a.add_argument('--check-json',action='append',default=[],help='構造化check JSON（argv配列、cwd、timeout等）')
    for name,help_text in [('status','読取りだけの状況確認'),('finalize','表示対象をローカルで確定'),('publish','明示指示のtopic公開'),('handoff','手渡し記録'),('acquire','Markdownだけを取得'),('confirm-content','内容確認を記録'),('correction','原文を保持して訂正依頼'),('publish-correction','訂正依頼だけ公開'),('plan','修正計画を保存'),('approve','人の計画承認を記録'),('submit','修正提出（独立検証前）'),('requa','元要求・前回指摘を保ち再QA'),('assess-residual','未検証事項のユーザー判断を記録'),('decide','終了判断（Git操作なし）')]:
        a=sub.add_parser(name,help=help_text);a.add_argument('--request');a.add_argument('--revision',type=int)
        if name=='finalize':a.add_argument('--commit');a.add_argument('--message');a.add_argument('--approved-path',action='append',default=[])
        if name in ['publish','publish-correction','approve']:a.add_argument('--message',required=True);a.add_argument('--approved-path',action='append',required=True)
        if name=='approve':a.add_argument('--plan-hash',required=True)
        if name=='acquire':
            g=a.add_mutually_exclusive_group();g.add_argument('--body',type=Path);g.add_argument('--branch');g.add_argument('--pr')
        if name=='confirm-content':a.add_argument('--evidence',required=True);a.add_argument('--checker',required=True)
        if name=='correction':a.add_argument('--reason',required=True)
        if name=='plan':a.add_argument('--input',type=Path,required=True)
        if name=='submit':a.add_argument('--target',action='append',required=True);a.add_argument('--evidence',required=True);a.add_argument('--unverified',action='append',default=[]);a.add_argument('--method')
        if name=='requa':a.add_argument('--audience',choices=['local','cloud']);a.add_argument('--reviewed');a.add_argument('--exclude',action='append',default=[]);a.add_argument('--check-json',action='append',default=[])
        if name=='assess-residual':a.add_argument('--message',required=True);a.add_argument('--reason',required=True)
        if name=='decide':a.add_argument('--message',required=True);a.add_argument('--residual',required=True)
    a=sub.add_parser('legacy',help='旧4成果物と原依頼を読取り照合');a.add_argument('--directory',type=Path,required=True);a.add_argument('--invite',type=Path,required=True)
    return p


def exclusions(values):
    result={}
    for value in values:
        if '=' not in value:raise QAError('対象外の指定はPATH=理由の形式が必要です')
        path,reason=value.split('=',1)
        if path in result:raise QAError('対象外のパスが重複しています')
        result[path]=reason
    return result


def checks_from(values):
    return [json.loads(value) for value in values]


def execute(a):
    if a.operation=='legacy':return read_legacy(a.directory,a.invite)
    if a.operation=='preflight':return gitops.status_preflight(a.root)
    w=Workflow(a.root);op=a.operation
    if op=='prepare':
        checks=checks_from(a.check_json)
        if a.required_test:
            raise QAError('--required-testは廃止予定です。--check-jsonでargv配列を指定してください')
        return w.prepare(a.purpose,a.criterion,a.target,a.implementer,a.author,a.audience,a.assumptions,a.baseline,a.reviewed,a.repository,exclusions(a.exclude),checks=checks)
    if op=='status':return w.status(a.request)
    revision=a.revision if a.revision is not None else w.store.select(a.request)['revision'];k={'revision':revision}
    if op=='finalize':return w.finalize(a.request,a.commit,a.message,a.approved_path,**k)
    if op=='publish':return w.publish(a.request,a.message,a.approved_path,**k)
    if op=='publish-correction':return w.publish_correction(a.request,a.message,a.approved_path,**k)
    if op=='handoff':return w.handoff(a.request,**k)
    if op=='acquire':return w.acquire(a.request,a.body,a.branch,a.pr,**k)
    if op=='confirm-content':return w.confirm_content(a.request,a.evidence,a.checker,**k)
    if op=='correction':return w.correction(a.request,a.reason,**k)
    if op=='plan':return w.plan(a.request,json.loads(a.input.read_text()),**k)
    if op=='approve':return w.approve(a.request,a.message,a.plan_hash,a.approved_path,**k)
    if op=='submit':return w.submit(a.request,a.target,a.evidence,a.unverified,a.method,**k)
    if op=='requa':return w.requa(a.request,a.audience,reviewed=a.reviewed,excluded=exclusions(a.exclude),checks=checks_from(a.check_json) if a.check_json else None,**k)
    if op=='assess-residual':return w.assess_residual(a.request,a.message,a.reason,**k)
    if op=='decide':return w.decide(a.request,a.message,a.residual,**k)
    raise QAError('未定義の操作です')


def main(argv=None):
    a=parser().parse_args(argv)
    try:result=execute(a);code=0
    except (QAError,OSError,ValueError,KeyError,TypeError) as e:
        result={'error':str(e),'next':{'担当':'ユーザーまたはローカル担当','操作':e.action if isinstance(e,QAError) else '入力・環境を確認して再実行してください','理由':str(e),'必要入力':'対象・承認・取得元の不足事項','依頼文':None}};code=2
    if a.json:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        if 'error' in result:print(f"確認待ち: {result['error']}")
        if a.operation=='preflight' and 'error' not in result:
            print(f"Git preflight: {'clean' if result['clean'] else 'dirty'} ／ 実装可能: {'はい' if result['safe_to_implement'] else 'いいえ'}")
            for key, label in [('repository_root','repo'),('branch','branch'),('head','HEAD'),('upstream','upstream'),('default_branch','既定branch')]:
                print(f"{label}: {result[key] or '不明'}")
            for key, label in [('staged','staged'),('unstaged','unstaged'),('untracked','untracked')]:
                print(f"{label}: {', '.join(result[key]) if result[key] else 'なし'}")
            print(result['next'])
        if 'id' in result:print(f"依頼 {result['id']} ／ サイクル {result['cycle']} ／ 状況 {result['phase']}")
        n=result.get('next',{})
        for label in ['担当','操作','理由','必要入力']:
            if n.get(label):print(f"{label}: {n[label]}")
        if n.get('依頼文'):print('\n渡す文書:\n'+n['依頼文'])
        for issue in result.get('issues',[]):print('確認事項: '+issue)
    return code


if __name__=='__main__':sys.exit(main())
