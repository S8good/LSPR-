Notes:
--------
1. The naming convention of python wrapper function follows closely with the C-API as much 
   as possible. For example, the C-API prefix (odapi/odapi_adv) were removed and the remaining 
   text were used as a python function name.

2. Set the enviromental variable below to point to <od_install_path>/lib folder:
   A. Linux / Mac
      LD_LIBRARY_PATH=/home/user1/OceanDirect_SDK-1.33.0/lib

3. For linux
   - libusb-1.0 library must be installed.
   - copy the rules file into the correct folder and either manually reload/trigger 
     the rules file or reboot your machine.

4. Add the following entry to the PYTHONPATH variable
     export PYTHONPATH=/home/user1/OceanDirect_SDK-1.33.0/python
