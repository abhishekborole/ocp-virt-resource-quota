"""Report live namespace quota headroom and optionally set one hard quota key."""
import argparse
from decimal import Decimal
import json
import sys
import subprocess
from datetime import datetime, timezone
from oc_client import Client, VM, VMI, MIG, SNAP, quantity, age_hours, condition, require_name, stopped, escape, migration


def execute(client,args):
    if args.quota_key:
        if not args.quota_value: raise ValueError('--quota-value is required')
        if quantity(args.quota_value) < 0: raise ValueError('Quota cannot be negative')
        quota = client.get('resourcequotas',require_name(args))
        return client.patch('resourcequotas',quota,[{'op':'add','path':'/spec/hard/'+escape(args.quota_key),'value':args.quota_value}],args.apply)
    return [{'name':q['metadata']['name'],'hard':q.get('status',{}).get('hard',{}),'used':q.get('status',{}).get('used',{})} for q in client.items('resourcequotas')]


def main():
    parser = argparse.ArgumentParser(description='Report live namespace quota headroom and optionally set one hard quota key.')
    parser.add_argument('--context',required=True,help='Explicit existing oc kubeconfig context')
    parser.add_argument('--namespace',required=True,help='Namespace for workload operations')
    parser.add_argument('--name',help='Exact workload/resource name where required')
    parser.add_argument('--apply',action='store_true',help='Execute the requested change; default is preview')
    parser.add_argument('--quota-key',help='ResourceQuota hard key, for example requests.cpu')
    parser.add_argument('--quota-value',help='New Kubernetes quantity')
    args = parser.parse_args()
    try:
        result = execute(Client(args.context,args.namespace),args)
        print(json.dumps({'context':args.context,'namespace':args.namespace,'collected_at':datetime.now(timezone.utc).isoformat(),'result':result},indent=2))
    except (RuntimeError,ValueError,KeyError,OSError,TimeoutError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
