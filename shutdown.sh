#!/bin/bash
while ! git push origin main; do
    echo "fallo "
    sleep 5
done 

echo "exito"
sudo shutdown now
