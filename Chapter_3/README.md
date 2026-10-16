# Chapter 3: TeraFlowSDN Parameterization & Deployment

This directory contains the deployment scripts developed in the context of **Chapter 3** of the diploma thesis for installing and deploying the ETSI TeraFlowSDN (TFS) controller.

---

## Contents
* `my_deploy.sh`: Customized deployment script (bash script) for launching TFS in a microK8s environment.

---

## Selective Microservice Activation

To conserve server computational resources and avoid resource-heavy subsystems outside the scope of this work (such as `opticalattackmitigator` or blockchain-based `dlt`), the script isolates and starts exclusively the required microservices:

```bash
export TFS_COMPONENTS="context device service pathcomp nbi webui slice"
```

For the overall deployment of TeraFlowSDN, it is recommended to follow the [official installation guide](https://tfs.etsi.org/documentation/develop/deployment_guide/) 

