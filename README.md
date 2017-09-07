

# uvs 0.3

uvs 0.3 development is hosted by uvs 0.2.1 alpha now. 
this repo is for archival purposes. 

# UVSource

UVSource (uvs for short) is an end to end encrypted distributed version control system. 
The problem uvs is trying to solve is that, "private repositories" on GitHub are not truly private in any reliable way. GitHub can see the repository in plaintext, and hence so can governments/criminals. 

The idea of end to end encrypted dvcs is encrypt everything put into the repository with a secure AEAD scheme (such as AES-GCM or even better XChaCha20, or good old AES-CBC-SHA256-HMAC) on the client machine. only send ciphertext to the cloud server, and when things are pulled from the cloud verify and decrypt on the client machine again, hence end to end encrypted dvcs. 

For more checkout uvs_slides.pdf 

# Install

uvs alpha was written on ubuntu, and isnt tested/ported to windows/MAC yet.
Windows and MAC will for sure be supported in the future, its just not done yet. 
Portable binaries are also planned for Win/Mac/Linux.


