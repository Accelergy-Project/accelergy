InstallPath=$1 # something like ~/.local/
cd $InstallPath/share/accelergy/estimation_plug_ins/
echo "Cloning plug-ins"
echo "$InstallPath/share/accelergy/estimation_plug_ins/"
echo "Cloning Aladdin plug-in"
git clone https://github.com/nelliewu95/accelergy-aladdin-plug-in.git
echo "Cloning CACTI plug-in"
git clone https://github.com/nelliewu95/accelergy-cacti-plug-in.git
cd accelergy-cacti-plug-in
echo "Cloning CACTI"
git clone https://github.com/HewlettPackard/cacti.git
cd cacti
echo "Building CACTI"
make -j2
echo "Done cloning plug-ins"
