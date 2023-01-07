import boto3
import json
import os
allowed_regions=os.getenv('ALLOWED_REGIONS')
max_instances=int(os.getenv('MAX_INSTANCES'))
print('allowed regions', allowed_regions, 'max instances',max_instances)
clients={}
for region in allowed_regions.split(','):
  clients[region] = boto3.client('ec2',region_name=region)

def numNonTerminatedInstances(client):
  useful_states=['pending','running','shutting-down','stopping','stopped']
  max_results=100
  ans=client.describe_instances(
    Filters=[{
      'Name': 'instance-state-name', 
      'Values':useful_states
    }],
    MaxResults=max_results
  )
  return sum(map(lambda r: len(r['Instances']), ans['Reservations']))

def numAllNonTerminatedInstances(clients):
  return sum(map(lambda client: numNonTerminatedInstances(client), clients.values()))

def enforceInstance(instanceId, region):
  num_instances=numAllNonTerminatedInstances(clients)
  print('checking instance', instanceId, region, region in allowed_regions, num_instances)
  client_for_deleting=None
  if region not in allowed_regions:
    client_for_deleting=boto3.client('ec2',region_name=region)
  elif num_instances > max_instances:
    client_for_deleting=clients[region]
  if client_for_deleting:
    try:
      print( client_for_deleting.terminate_instances(InstanceIds= [instanceId]) )
    except Exception as e:
      print('problem deleting instance', instanceId, e)
  else:
    print('Allowing instance', instanceId, region)

def handler(event, context):
  print('event ...', event)
  region=event['region']
  instance_id=event['detail']['instance-id']
  enforceInstance(instance_id,region)