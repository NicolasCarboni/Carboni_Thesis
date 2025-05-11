const HashStorage = artifacts.require("HashStorage");

module.exports = function(deployer) {
  deployer.deploy(HashStorage)
    .then(() => {
      console.log("Contract deployed at address:", HashStorage.address);
    });
};
