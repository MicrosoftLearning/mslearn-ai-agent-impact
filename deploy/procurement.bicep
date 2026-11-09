targetScope = 'resourceGroup'
param location string
param environmentName string
param appName string
param identityName string
param registryName string
param image string
@description('JSON matching runtime Settings; contains IDs only, never credentials.')
param runtimeConfig string

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = { name: registryName }
resource pull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, 'AcrPull')
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: { workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }] }
}
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identity.id}': {} } }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: { external: true, targetPort: 8088, allowInsecure: false, transport: 'http' }
      registries: [{ server: registry.properties.loginServer, identity: identity.id }]
    }
    template: {
      containers: [{
        name: 'procurement'
        image: image
        env: [{ name: 'CALDOVA_CONFIG', value: runtimeConfig }, { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId }]
        resources: { cpu: json('0.5'), memory: '1Gi' }
        probes: [{ type: 'Readiness', httpGet: { path: '/readiness', port: 8088 }, initialDelaySeconds: 10, periodSeconds: 10 }]
      }]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
  dependsOn: [pull]
}
output apiUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
output principalId string = identity.properties.principalId
output clientId string = identity.properties.clientId
