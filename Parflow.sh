#!/bin/bash
echo "Content-type: text/html"
echo ""
echo ""

#readonly appLocation="/srv/http/data/Parflow.sif"
readonly appLocation="/var/www/subset/app/Parflow.sif"
#readonly outLocation="/srv/http/out/"
readonly outLocation="/var/www/subset/out/"

readonly urlPattern="http://subset.cuahsi.org/download-gzip/([0-9]|[a-z]){40}" #Ensure valid URL

if ! [[ $1 =~ $urlPattern ]]; then
    echo "Invalid URL, must be of the form " $urlPattern " got " $1
    exit
fi

echo "Valid URL, downloading"
echo "<br>"

readonly originalDir=$PWD

readonly tmpDir=$(mktemp -d)
cd $tmpDir

if ! wget -q -O data.tar.gz $1; then
	cd $originalDir
	rm -r $tmpDir

    	echo "Unable to download data."
    	exit 1
fi

echo "Downloaded, extracting data"
echo "<br>"
tar -xf data.tar.gz --strip-components=1
rm data.tar.gz

echo "Data extracted. Running ParFlow"
echo "<br>"
if ! singularity run $appLocation simulation.tcl 2>&1 >_; then
	echo "Parflow returned with an error:<br>"
	cat _

	cd $originalDir
	rm -r $tmpDir
	exit 1
fi
rm _

#cp /srv/http/data/cuahsi-subset.txt .
cp /var/www/subset/data/cuahsi-subset.txt .
cp /var/www/subset/post_proc/CONUS1_to_USGS.csv .
#cp /srv/http/data/PFPostProc/CONUS1_to_USGS.csv .

echo "Generating images"
echo "<br>"

readonly id=$(echo $1 | sed 's/.*(([0-9]|[a-z]){40}).*/\1/' -E)

#readonly gaugeLocator="/srv/http/data/PFPostProc/GaugeLocator.py"
readonly gaugeLocator="/var/www/subset/post_proc/GaugeLocator.py"

readonly outDir=$outLocation$id

rm -r $outDir #Delete if exists @@TODO remove
mkdir -p $outDir/flows
readonly python="/var/www/subset/post_proc/.envs/bin/python"
if ! $python $gaugeLocator --pf_outputs $tmpDir --out_dir $outDir/flows --print_png true 2>&1 >_; then
    echo "Gauge Locator returned with an error:<br>"
    cat _

	cd $originalDir
	rm -r $tmpDir
	exit 1
fi
rm _

rm CONUS1_to_USGS.csv
cp -r $outDir/flows .

echo "Copied Files<br>"

readonly outFile=$outDir".tar.gz"


tar -czf $outFile *

echo "Done, " $(ls -l | wc -l) " files"
echo "<br>"

if ! mv $outFile $outDir 2>&1 >_; then
	echo "Failed to move file<br>"
	cat _

	cd $originalDir
	rm -r $tmpDir
	exit 1
fi

cd $originalDir
rm -r $tmpDir
#readonly htmlGenerator="/srv/http/data/PFPostProc/PageGenerator.py"
readonly htmlGenerator="/var/www/subset/post_proc/PageGenerator.py"
#if ! /srv/http/data/PFPostProc/.envs/bin/python $htmlGenerator --png_dir $outDir/flows/png --zip_file $outDir/$outfile 2>&1 >_; then
#    echo "HTML Generator returned with an error:<br>"
#    cat _
#    
#        cd $originalDir
#        rm -r $tmpDir
#        exit 1
#fi
#echo Content-type: text/html
#echo $outDir/flows/png
#echo $outDir/$outfile/$id.tar.gz
html=$($python $htmlGenerator --png_dir $outDir/flows/png --zip_file $outDir/$outfile/$id.tar.gz)
echo $html
