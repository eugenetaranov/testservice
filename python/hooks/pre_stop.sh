#!/bin/bash

#for i in {1..60}
for i in {1..300}
do
   echo $(date +%F_%T) ${i} >&2
   sleep 1
done
