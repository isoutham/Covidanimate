for i in 'Germany' 'England,Wales' 'Netherlands' 'Belgiun'
do
    echo $i
    python3.8 ./animate.py -a -c $i
    mv choropleth.mp4 $i.mp4
done

