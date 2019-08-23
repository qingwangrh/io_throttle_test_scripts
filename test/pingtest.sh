for ((i=0;i<8;i++))
do
let idx=69+$i
ping -c 1 vm-17-$idx > /dev/null
if (($? !=0));then
echo "$i: XXXXXX"
fi


done
