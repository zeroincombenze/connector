#!/bin/bash

for port in 8172 8170; do
  for ctr in {11..0}; do
      ss -lt|grep 0.0.0.0:$port
      [[ $? -eq 0 ]] && break
      [[ $port -ge 8200 ]] && vid="oca$((port-8260))" || vid="odoo$((port-8160))"
      echo "No Odoo instance running found at port $port ($vid)"
      echo odooctl restart $vid
      odooctl restart $vid
      sleep 5
  done
  [[ $ctr -eq 0 ]] && exit 1
done
[[ $ctr -eq 0 ]] && exit 1
msg=""
psql -Atl|grep -E "^demo10\|" || msg="$msg DB demo10 not found!"
psql -Atl|grep -E "^demo12\|" || msg="$msg DB demo12 not found!"
# psql -Atl|grep -E "^demo14\|" || msg="$msg DB demo14 not found!"
# psql -Atl|grep -E "^demo16\|" || msg="$msg DB demo16 not found!"
# psql -Atl|grep -E "^demo18\|" || msg="$msg DB demo18 not found!"

[[ -n $msg ]] && echo $msg && exit 1
exit 0
