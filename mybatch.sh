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
#SBATCH --array=1-160

module load StdEnv/2020
module load python/3.9.6
# module load mujoco python
# python -c "import mujoco"
source /home/payamp/ENV3/bin/activate

# . $CONDA_ROOT/etc/profile.d/conda.sh

echo 'running code'
# Run Python file
# wandb offline

declare -a arg1=(214 215 216 217)
declare -a arg2=(2)
declare -a arg3=(5e-3 1e-2 5e-2 1e-1 5e-1 1e0 5e0 0)
declare -a arg4=(1e2 5e2 1e3 5e3 1e4)
declare -a arg5=(1e-12)

declare -a params
COUNTER=0
for ar1 in ${arg1[@]}
do
for ar2 in ${arg2[@]}
do
for ar3 in ${arg3[@]}
do
for ar4 in ${arg4[@]}
do
for ar5 in ${arg5[@]}
do
COUNTER=$[$COUNTER +1]
params[$COUNTER]={$ar1,$ar2,$ar3,$ar4,$ar5,esults_arg1_${ar1}_arg2_${ar2}_arg3${ar3}_arg4${ar4}_arg5${ar5}}
done
done
done
done
done

ids=${params[$SLURM_ARRAY_TASK_ID]}

IFS=',' read -r -a array <<< "${ids:1:${#ids}-2}"

echo ${array[0]}
echo ${array[1]}
echo ${array[2]}
echo ${array[3]}
echo ${array[4]}

python3 train.py --seed ${array[0]} --ar_case ${array[1]} --lambda_P ${array[2]} --c_homog ${array[3]} --noise_a2ps ${array[4]}
