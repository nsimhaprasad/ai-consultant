# Baid IntelliJ Plugin Deployment Guide

This guide covers the deployment process for the Baid IntelliJ plugin, including configuration, environment setup, and CI/CD pipeline details.

## Table of Contents
- [Configuration Overview](#configuration-overview)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment Process](#deployment-process)
- [Troubleshooting](#troubleshooting)

## Configuration Overview

The Baid plugin uses a hierarchical configuration system:
1. Default properties file (`baid-config.properties`)
2. Environment variables (override properties file)
3. Build-time configurations

### Configuration Files

#### `BaidConfiguration.kt`
Main configuration class that loads settings from properties file and environment variables.

#### `baid-config.properties`
Default configuration values for development environment.

```properties
# Google OAuth Configuration
google.client.id=742371152853-usfgd7l7ccp3mkekku8ql3iol5m3d7oi.apps.googleusercontent.com
google.redirect.uri=http://localhost:8080/api/auth/google-login
google.auth.endpoint=https://accounts.google.com/o/oauth2/auth
google.scope=email profile
google.access.type=offline
google.prompt=consent

# Backend Configuration
backend.url=http://localhost:8080
backend.api.endpoint=/consult

# Credential Store Keys
credential.backend.token.key=baid_backend_token
credential.token.expiry.key=baid_token_expiry
```

## Environment Variables

The following environment variables can be used to override default configurations:

| Variable | Description | Example |
|----------|-------------|---------|
| `BAID_CLIENT_ID` | Google OAuth Client ID | `xxxxx.apps.googleusercontent.com` |
| `BAID_REDIRECT_URI` | OAuth redirect URI | `https://api.baid.tech/auth/callback` |
| `BAID_AUTH_ENDPOINT` | Google OAuth endpoint | `https://accounts.google.com/o/oauth2/auth` |
| `BAID_SCOPE` | OAuth scope | `email profile` |
| `BAID_ACCESS_TYPE` | OAuth access type | `offline` |
| `BAID_PROMPT` | OAuth prompt | `consent` |
| `BAID_BACKEND_URL` | Backend server URL | `https://api.baid.tech` |
| `BAID_API_ENDPOINT` | API endpoint path | `/consult` |
| `BAID_BACKEND_TOKEN_KEY` | Token storage key | `baid_backend_token` |
| `BAID_TOKEN_EXPIRY_KEY` | Token expiry key | `baid_token_expiry` |
| `BAID_ACCESS_TOKEN` | Static access token (optional) | `your-access-token` |

## Local Development

### Prerequisites
- JDK 17
- IntelliJ IDEA (recommended)
- Gradle

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/baid-plugin.git
   cd baid-plugin/intelij-plugin
   ```

2. **Configure environment**
   Create a `.env` file in the project root:
   ```bash
   # Development environment
   BAID_BACKEND_URL=http://localhost:8080
   BAID_REDIRECT_URI=http://localhost:8080/api/auth/google-login
   ```

3. **Run the plugin**
   ```bash
   ./gradlew runIde
   ```

### Development Tips
- The plugin uses `BaidConfiguration.getInstance()` to access configuration
- Configuration is loaded once at startup
- Restart the IDE to apply environment variable changes

## CI/CD Pipeline

### Pipeline Overview

The GitHub Actions workflow includes the following jobs:
1. **Build** - Compiles and packages the plugin
2. **Test** - Runs unit and integration tests
3. **Verify** - Validates plugin compatibility
4. **Publish** - Deploys to JetBrains Marketplace

### Environment Configuration

#### GitHub Secrets

Set the following secrets in your GitHub repository:

- **Development**
  - `BAID_BACKEND_URL` = `http://dev-api.baid.tech`
  - `BAID_CLIENT_ID` = Development OAuth client ID
  - `BAID_REDIRECT_URI` = Development redirect URI

- **Staging**
  - `BAID_BACKEND_URL` = `https://staging-api.baid.tech`
  - `BAID_CLIENT_ID` = Staging OAuth client ID
  - `BAID_REDIRECT_URI` = Staging redirect URI

- **Production**
  - `BAID_BACKEND_URL` = `https://api.baid.tech`
  - `BAID_CLIENT_ID` = Production OAuth client ID
  - `BAID_REDIRECT_URI` = Production redirect URI
  - `INTELLIJ_PUBLISH_TOKEN` = JetBrains Marketplace token

## Deployment Process

### Automatic Deployment

The CI/CD pipeline automatically:
1. Builds and tests on every PR
2. Deploys to development on main branch merge
3. Requires manual approval for production

### Manual Deployment

To manually trigger a deployment:

1. **Navigate to Actions tab** in GitHub
2. **Select "Jetbrains Plugin" workflow**
3. **Click "Run workflow"**
4. **Select environment** (development/staging/production)
5. **Enter version** (optional) if needed
6. **Click "Run workflow"**

### Environment-Specific Deployments

#### Development
- Automatically deploys on main branch
- Uses development configuration
- No manual approval required

#### Staging
- Triggered manually via workflow dispatch
- Uses staging configuration
- Requires manual approval

#### Production
- Triggered manually via workflow dispatch
- Uses production configuration
- Requires manual approval
- Publishes to JetBrains Marketplace

## Configuration Management

### Backend URL Configuration

The plugin connects to different backend environments:

| Environment | Backend URL |
|-------------|-------------|
| Local | `http://localhost:8080` |
| Development | `http://dev-api.baid.tech` |
| Staging | `https://staging-api.baid.tech` |
| Production | `https://api.baid.tech` |

### OAuth Configuration

Each environment has its own OAuth client:

1. **Development**: OAuth client configured for localhost callbacks
2. **Staging**: OAuth client for staging domain
3. **Production**: OAuth client for production domain

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify OAuth client ID matches environment
   - Check redirect URI configuration
   - Ensure backend is running and accessible

2. **API Connection Errors**
   - Validate backend URL environment variable
   - Check network connectivity
   - Verify backend API is running

3. **Token Storage Issues**
   - Clear token storage keys if needed
   - Check credential store permissions

### Debug Commands

```bash
# Test configuration loading
./gradlew test --tests ConfigurationTest

# Verify plugin in sandbox
./gradlew runIde

# Check plugin package
./gradlew buildPlugin
unzip -l build/distributions/plugin.zip
```

## Security Considerations

1. **Never commit sensitive credentials** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate tokens regularly** in production
4. **Review access logs** for suspicious activity

## Version Management

The plugin follows semantic versioning:
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

Version can be specified during manual deployment or auto-incremented by CI/CD.