import subprocess
import os
import click
import time

@click.command()
@click.option('--gpu', default=True, type=bool)
def launch_experiments(gpu):
    for i in range(8):
        ####################EDIT THESE FIELDS##################
        username = f'adibellathur' # your google username
        algorithm = f'pearl'
        # gpu zones are 'us-central1-a' 'us-east1-c' 'europe-west1-b' 'asia-east1-a' 'asia-east1-b'
        zone = f'europe-west1-b' # find the apprpropriate zone here https://cloud.google.com/compute/docs/regions-zones
        instance_name = f'v2-pearl-{i}'
        bucket = f'ml1/round1/pearl/v2'
        branch = 'adi-new-metaworld-results-ml1-mt1'
        experiment = f'metaworld_launchers/ml10/pearl_metaworld_ml10.py'
        ######################################################

        if not gpu:
            machine_type =  'n2-standard-8' # 'c2-standard-4' we have a quota of 24 of each of these cpus per zone.
            # You can use n1 cpus which are slower, but we are capped to a total of 72 cpus per zone anyways
            docker_run_file = 'docker_metaworld_run_cpu.py' # 'docker_metaworld_run_gpu.py' for gpu experiment
            docker_build_command = 'make run-headless -C ~/garage/'
            source_machine_image = 'cpu-instance-2'
            launch_command = (f"gcloud beta compute instances create {instance_name} "
                f"--metadata-from-file startup-script=launchers/launch-experiment-{algorithm}-{i}.sh --zone {zone} "
                f"--source-machine-image {source_machine_image} --machine-type {machine_type}")
        else:
            machine_type =  'n1-standard-4'
            docker_run_file = 'docker_metaworld_run_gpu.py'
            docker_build_command = ("make run-nvidia-headless -C ~/garage/ "
                '''PARENT_IMAGE='nvidia/cuda:11.0-cudnn8-runtime-ubuntu18.04' ''')
            source_machine_image = 'metaworld-v2-gpu-instance'
            accelerator = '"type=nvidia-tesla-k80,count=1"'
            launch_command = (f"gcloud beta compute instances create {instance_name} "
                f"--metadata-from-file startup-script=launchers/launch-experiment-{algorithm}-{i}.sh --zone {zone} "
                f"--source-machine-image {source_machine_image} --machine-type {machine_type} "
                f'--accelerator={accelerator}')

        os.makedirs('launchers/', exist_ok=True)

        script = (
        "#!/bin/bash\n"
        f"cd /home/{username}\n"
        f"cp -r /home/avnishnarayan/.mujoco /home/{username}/"
        f'runuser -l {username} -c "git clone https://github.com/rlworkgroup/garage'
            f' && cd garage/ && git checkout {branch} && mkdir data/"\n'
        f'runuser -l {username} -c "mkdir -p metaworld-runs-v2/local/experiment/"\n'
        f'runuser -l {username} -c "{docker_build_command}"\n'
        f'''runuser -l {username} -c "cd garage && python {docker_run_file} '{experiment}'"\n'''
        f'runuser -l {username} -c "cd garage/metaworld_launchers && python upload_folders.py {bucket} 1200"\n')

        with open(f'launchers/launch-experiment-{algorithm}-{i}.sh', mode='w') as f:
            f.write(script)
        if not (i % 4) and i!=0:
            time.sleep(500)
        subprocess.Popen([launch_command], shell=True)
        print(launch_command)
    time.sleep(300)

launch_experiments()