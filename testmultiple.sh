# usage: testmultiple.sh <number of iterations to run>
i=0
while [ $i -lt $1 ]
do
python TestHarness.py -s Sender.py -r Receiver.py | grep fail
i=$[$i+1]
done
