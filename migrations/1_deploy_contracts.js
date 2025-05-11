const DataFactModel = artifacts.require("DataFactModel");

module.exports = function(deployer) {
  deployer.deploy(DataFactModel);
};
