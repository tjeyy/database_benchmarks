
#!/bin/bash
sudo useradd gpadmin -r -m -g gpadmin
sudo chsh gpadmin -s /bin/bash
sudo passwd gpadmin

su gpadmin
ssh-keygen -t rsa -b 4096
ssh-copy-id nemea
exit
