# G.H.O.S.T.
Guardian, Host, and Operational Scribe Tool for batserver


## Future Roadmap

### V0
- run langchain agent that can automatically read the readme.md file and operational_manual.md as instructions and input the text that user will send to him.
- after input, model outputs the result


### V1
- create filedirectory instructions (main file - README.md, service specified files in `docs/` directory

- Open and edit file (automatically open and edit the readme.md file of system configuration)
- Open directory and edit specified file (automatically open the service specified file for example nextcloud.md and edit it)

- track changelog history, what was changed by agent (ghost should maintain this file also `changelog.md`)

### V2
- run commands to get realtime information (docker ps, htop, nvidia-smi to automatically fill the information about the hardware and so on.)
