import boto3
import logging
import json

# Crea clientes para el EC2 y Ruta53
ec2_client = boto3.client('ec2')
route53_client = boto3.client('route53')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_instance_public_ip(instance_id):
    try:
        # Obtener la IP publica de la instancia
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        public_ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        
        if public_ip:
            return public_ip
        else:
            raise ValueError(f"Public IP for instance {instance_id} was not found")

    except Exception as e:
        logger.error(f"Error obtaining public IP for instance: {instance_id}: {str(e)}")
        raise


def lambda_handler(event, context):
    try:
        instance_id = event['detail']['instance-id']
        state = event['detail']['state']
        tags = event['detail']['tags']
        public_ip = get_instance_public_ip(instance_id)
       
        logger.info(f"Received state-change event for instance: {instance_id}, new state: {state}")
        
        
        if state == 'running':
            dns_names = None
            for tag in tags:
                if tag['Key'] == 'DNS_NAMES':
                    dns_names = tag['Value']
                    break

            if not dns_names:
                logger.error(f"No DNS_NAMES tag found for instance: {instance_id}")
                return {'statusCode': 400, 'body': 'DNS_NAMES tag not found'}

            # Separar los nombres DNS con comas.
            dns_names_list = dns_names.split(',')
            hosted_zone_id = 'Z06113313M7JJFJ9M7HM8'

            changes = []
            for dns_name in dns_names_list:
                changes.append({
                    'Action': 'UPSERT',  
                    'ResourceRecordSet': {
                        'Name': f"{dns_name}.campusdual.mkcampus.com",
                        'Type': 'A',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': public_ip}]  
                    }
                })

            
            response = route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={'Changes': changes}
            )
            logger.info(f"Successfully updated DNS records for instance {instance_id}: {response}")
            return {'statusCode': 200, 'body': 'DNS records updated successfully'}

    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {'statusCode': 500, 'body': f"Error: {str(e)}"}
    