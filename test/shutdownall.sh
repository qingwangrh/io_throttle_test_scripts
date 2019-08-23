for ((i=0;i<8;i++))
do
let idx=69+$i
ssh  vm-17-$idx poweroff
done
