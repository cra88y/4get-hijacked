# Task: Optimize Docker Compose for Coolify Responsiveness

## Plan
- [x] Analyze current docker-compose.yml configuration
- [x] Identify Coolify-specific optimization opportunities
- [x] Research Coolify best practices for Docker Compose
- [x] Document recommendations for improved responsiveness
- [x] Create optimized docker-compose.yml version

## Research Log

### Current Configuration Analysis
- Found docker-compose.yml with 3 services: searxng, valkey, 4get-hijacked
- All services use `restart: always` policy
- Services are interconnected with dependencies and shared network
- Volume mounts are used for configuration and data persistence
- searxng depends_on valkey and 4get-hijacked
- All services are on searxng-net bridge network

### Coolify Optimization Opportunities
- Health checks for better service monitoring
- Resource limits for predictable performance
- Graceful shutdown configurations
- Coolify-specific labels and metadata
- Service dependencies optimization
- Startup order and readiness indicators

### Recommendations for Improved Responsiveness

#### 1. Add Health Checks
- Add health checks to all services to help Coolify monitor service status
- This allows Coolify to make better decisions about service readiness

#### 2. Configure Resource Limits
- Add CPU and memory limits to prevent resource contention
- This makes the services more predictable and manageable by Coolify

#### 3. Optimize Service Dependencies
- Current depends_on is basic - enhance with condition-based dependencies
- Use health checks to determine when dependencies are truly ready

#### 4. Add Coolify-Specific Labels
- Add labels that Coolify can use for better integration and monitoring
- Include metadata about service types and priorities

#### 5. Graceful Shutdown Configuration
- Configure proper shutdown timeouts to allow services to exit cleanly
- This prevents data corruption and ensures proper cleanup

#### 6. Network Optimization
- Consider using host networking for better performance if appropriate
- Or optimize the bridge network configuration

## Specific Implementation Recommendations

### For searxng service:
- Add health check endpoint (likely /health or similar)
- Configure resource limits based on expected load
- Add Coolify labels for service type and priority

### For valkey service:
- Add Redis-specific health check
- Configure memory limits appropriate for caching
- Add persistence configuration if needed

### For 4get-hijacked service:
- Add health check for the web service
- Configure resource limits based on scraping workload
- Add labels indicating it's a worker/service type

### General Coolify Best Practices:
- Use Coolify's built-in health monitoring features
- Configure proper service scaling if needed
- Set up appropriate logging and monitoring
- Consider using Coolify's secret management for sensitive data

## Summary of Key Improvements

### 1. Critical Python Path Fix
- **CRITICAL ISSUE FOUND**: The `google-4get.py` and other 4get engines are failing because they can't import `fourget_hijacker_client`
- **ROOT CAUSE**: Python path not set up correctly in the container
- **SOLUTION**: Added `PYTHONPATH` environment variable to include the searx engines directory

### 2. Health Checks Added
- **searxng**: HTTP health check on /healthz endpoint (30s interval, 10s timeout)
- **valkey**: Redis ping command health check (15s interval, 5s timeout)
- **4get-hijacked**: HTTP health check on root endpoint (30s interval, 10s timeout)
- All health checks have appropriate intervals, timeouts, and retry configurations

### 2. Resource Management
- **CPU Limits**: Set appropriate limits for each service (searxng: 2.0, valkey: 1.0, 4get-hijacked: 1.5)
- **Memory Limits**: Configured memory limits and reservations for predictable performance
- **Reservations**: Minimum guaranteed resources for each service

### 3. Improved Service Dependencies
- Changed from basic `depends_on` to condition-based dependencies
- searxng now waits for valkey to be `service_healthy` instead of just started
- This ensures proper service readiness before dependent services start

### 4. Coolify-Specific Enhancements
- Added Coolify labels for service classification and priority
- Service type labels (search, cache, scraper)
- Priority labels (high, medium) for Coolify orchestration
- Worker/service type indicators

### 5. Restart Policy Optimization
- Changed from `restart: always` to `restart: unless-stopped`
- Provides better control while maintaining reliability

### 6. Network Optimization
- Made network attachable for potential future container additions
- Maintained bridge network for isolation

### 7. Volume Configuration
- Added explicit volume naming for better management
- Maintained persistent storage for valkey data

## Migration Notes

### CRITICAL FIXES REQUIRED
1. **Python Path Issue**: The most critical issue is that the 4get engines (google-4get.py, brave-4get.py, etc.) cannot import `fourget_hijacker_client`
   - **Solution**: Added `PYTHONPATH=/usr/local/searxng/searx/engines` environment variable
   - **Verification**: Check that all 4get engines can now import the module properly

### Testing & Validation
2. **Testing**: Test the new configuration in a staging environment first
3. **Health Check Endpoints**: Verify that the health check endpoints exist and work:
   - searxng should have a /healthz endpoint
   - 4get-hijacked should respond to HTTP requests on /
4. **4get Engine Validation**: Confirm that google-4get, brave-4get, duckduckgo-4get, and yandex-4get engines all load successfully

### Performance Tuning
5. **Resource Tuning**: Adjust CPU/memory limits based on your specific hardware and workload
6. **Coolify Integration**: Ensure Coolify can interpret the labels and health status correctly
7. **Backup**: Backup your current configuration and data before migrating

### Monitoring & Observability
8. **Log Monitoring**: Watch for any remaining import errors or engine loading issues
9. **Health Check Monitoring**: Verify all health checks pass consistently
10. **Resource Usage**: Monitor CPU/memory usage to validate the resource limits are appropriate