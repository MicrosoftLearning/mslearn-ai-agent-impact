targetScope = 'resourceGroup'
param location string
param accountName string
param projectName string
param modelDeploymentName string
param modelName string
param modelVersion string
param modelFormat string = 'OpenAI'
param modelSkuName string
param modelCapacity int

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: account
  name: projectName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: { displayName: projectName, description: 'Isolated Caldova L400 training project' }
}
resource model 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: account
  name: modelDeploymentName
  sku: { name: modelSkuName, capacity: modelCapacity }
  properties: { model: { format: modelFormat, name: modelName, version: modelVersion } }
}
output projectId string = project.id
output projectIdentity string = project.identity.principalId
output accountId string = account.id
output modelDeployment string = model.name
output endpoint string = 'https://${accountName}.services.ai.azure.com/api/projects/${projectName}'
