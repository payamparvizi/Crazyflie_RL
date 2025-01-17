#!/bin/bash

# Specify the partition of the cluster to run on (Typically TrixieMain)
#SBATCH --job-name=adaptiveOpticsRL
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G
# Add your project account code using -A or --account
#SBATCH --account=def-dspinell
# Specify the time allocated to the job. Max 12 hours on TrixieMain queue.
#SBATCH --time=3:00:00
# Request GPUs for the job. In this case 4 GPUs
#SBATCH --gres=gpu:p100:1
#SBATCH --mail-user=pparv056@uottawa.ca
#SBATCH --mail-type=ALL
#SBATCH --chdir=/scratch/payamp/
#SBATCH --signal=B:USR1@30
#SBATCH --array=1-10

module load StdEnv/2020
module load python/3.9.6
# module load mujoco python
# python -c "import mujoco"
source /home/payamp/ENV3/bin/activate

# . $CONDA_ROOT/etc/profile.d/conda.sh

echo 'running code'
# Run Python file
# wandb offline

declare -a arg1=(1 2 3 4 5 6 7 8 9 10)

declare -a params
COUNTER=0
for ar1 in ${arg1[@]}
do
COUNTER=$[$COUNTER +1]
params[$COUNTER]={$ar1,esults_arg1_${ar1}}
done

ids=${params[$SLURM_ARRAY_TASK_ID]}

IFS=',' read -r -a array <<< "${ids:1:${#ids}-2}"

echo ${array[0]}

python3 train.py --seed ${array[0]}
