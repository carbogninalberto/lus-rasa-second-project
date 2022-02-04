# Introduction

In this project I developed a simple conversational agent using the rasa framework.

final video result can be found [here](https://drive.google.com/drive/folders/1D-OptiE8L9G-7af546Xr5HDIiDbdkrjQ?usp=sharing)

## RASA Requirements

It is very important that you have the following compatible versions of rasa, rasa sdk and rasa X.

```
Rasa Version      :         2.8.14
Minimum Compatible Version: 2.8.9
Rasa SDK Version  :         2.8.3
Rasa X Version    :         0.42.6
Python Version    :         3.8.10
Operating System  :         Linux-5.4.0-94-generic-x86_64-with-glibc2.29
Python Path       :         /usr/bin/python3
```

# How to
Before starting run the the custom actions server with:

```bash
rasa run actions
```
Then, to train the model run:

```bash
rasa train
```
to test it:

```bash
rasa shell
```
to check metadata:

```bash
rasa shell nlu
```

to run rasa x:
```
rasa x
```

```
rasa test nlu --nlu data/nlu.yml --cross-validation --config pipelines/config.base.yml pipelines/config.variant_1.yml pipelines/config.variant_2.yml pipelines/config.variant_3.yml
```
