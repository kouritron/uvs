

# uvs 0.3

uvs 0.3 development is hosted by uvs 0.2.1 alpha now. 
this repo is for archival purposes. 

# UVSource

UVSource (uvs for short) is an end to end encrypted distributed version control system. 
The problem uvs is trying to solve is that, "private repositories" on GitHub are not truly private in any reliable way. GitHub can see the repository in plaintext, and hence so can governments/criminals. 

The idea with end to end encrypted dvcs is simple. Just encrypt everything put into the repository on the client machine, with a secure AEAD scheme (such as AES-GCM or XChaCha20, or just plain old AES-CBC-SHA256-HMAC). Then when pushing to a cloud hosting service like GitHub, send only ciphertext. And when things are pulled from the cloud service verify then decrypt, again on the client machine and give the files to the user. Hence end to end encrypted dvcs. 

For more checkout uvs_slides.pdf 

# Install

uvs alpha was written on ubuntu, and isnt tested/ported to windows/MAC yet.
Windows and MAC will for sure be supported in the future, its just not done yet. 
Portable binaries are also planned for Win/Mac/Linux.


