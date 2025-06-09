# Blueprint Migration Plan for Data Analyzer

This document outlines the plan for migrating the legacy blueprints in the `modules/routes/` directory to the new application structure with blueprints in the `app/` directory.

## Current Blueprint Inventory

### Legacy Blueprints (modules/routes/)

1. **home_bp** (modules/routes/home.py)
   - Main functionality: Display home page, analyze tickers
   - Key routes: `/` (index), `/analyze`
   - Dependencies: price_history, chart_creator modules

2. **graphs_bp** (modules/routes/graphs.py)
   - Main functionality: Display graph visualization pages
   - Key routes: `/graphs`
   - Dependencies: Chart creation utilities

3. **valuations_bp** (modules/routes/valuations.py)
   - Main functionality: Financial valuations and analysis
   - Key routes: `/valuation`
   - Dependencies: Financial calculation modules

4. **placeholders_bp** (modules/routes/placeholders.py)
   - Main functionality: Placeholder routes for future functionality
   - Key routes: Various placeholder endpoints
   - Dependencies: Minimal

### New Blueprint Structure (app/)

1. **main** (app/main/)
   - Current functionality: Acts as a wrapper/redirect to home_bp
   - Target functionality: Should absorb home_bp functionality

2. **auth** (app/auth/)
   - Current functionality: Authentication (login, register, logout)
   - Status: Complete, no changes needed

3. **admin** (app/admin/)
   - Current functionality: User management
   - Status: Complete, no changes needed

## Migration Strategy

### Phase 1: Preparation and Analysis (2-3 days)

1. **Detailed Blueprint Analysis**
   - Create detailed documentation of each legacy blueprint's functionality
   - Map all routes and their dependencies
   - Identify integration points with other parts of the application

2. **Determine Migration Order**
   - Based on dependencies, define the optimal order for migration
   - Proposed order: placeholders_bp → graphs_bp → valuations_bp → home_bp

3. **Define New Blueprint Structure**
   - Decide whether to create new blueprints (e.g., graphs, valuations) or consolidate into main
   - Create skeleton blueprint files and directory structure

### Phase 2: Implementation (1-2 weeks)

#### Step 1: Migrate placeholders_bp (1 day)
   - Create app/placeholders/ directory if keeping as separate blueprint
   - Move routes to app/placeholders/routes.py or app/main/routes.py if consolidating
   - Update imports and dependencies
   - Test each route

#### Step 2: Migrate graphs_bp (2-3 days)
   - Create app/graphs/ directory
   - Move routes to app/graphs/routes.py
   - Move graph-specific templates to app/templates/graphs/
   - Update template references
   - Test all graph functionality

#### Step 3: Migrate valuations_bp (2-3 days)
   - Create app/valuations/ directory
   - Move routes to app/valuations/routes.py
   - Move valuation-specific templates to app/templates/valuations/
   - Update template references
   - Test all valuation functionality

#### Step 4: Migrate home_bp (3-4 days)
   - This is the most critical migration as it contains core functionality
   - Move routes to app/main/routes.py
   - Update all template references
   - Test thoroughly

### Phase 3: Legacy Blueprint Removal (2-3 days)

1. **Update Blueprint Registration**
   - Remove the `register_legacy_blueprints` function from app/main/routes.py
   - Update `_register_blueprints` in app/__init__.py to register all new blueprints

2. **Clean Up Imports**
   - Remove imports of legacy blueprints from throughout the codebase
   - Update any remaining references

3. **Final Testing**
   - Comprehensive testing of all application functionality
   - Verify all routes work correctly under the new structure

## Testing Strategy

For each blueprint migration:

1. **Unit Testing**
   - Test each route function in isolation
   - Verify correct response codes and template rendering

2. **Integration Testing**
   - Test flows that span multiple routes
   - Verify correct data passing between routes

3. **User Interface Testing**
   - Manual testing of all UI elements
   - Verify forms, charts, and interactive elements work as expected

4. **Regression Testing**
   - Run full test suite after each migration
   - Verify no regressions in previously working functionality

## Migration Tools

To facilitate the migration, we can create additional tools:

1. **Blueprint Route Analyzer**
   - A script to analyze and document all routes in legacy blueprints
   - Output a detailed mapping of routes, methods, and dependencies

2. **Blueprint Migration Helper**
   - Automate the process of moving routes between blueprints
   - Handle template path updates and import changes

3. **Route Testing Tool**
   - Automatically test all routes after migration
   - Compare responses before and after migration

## Rollback Plan

If issues arise during migration:

1. Restore from backup for the affected blueprint
2. Revert the blueprint registration in app/__init__.py
3. Update any modified imports
4. Test to ensure rollback was successful

## Conclusion

This phased approach allows for systematic migration of functionality from the legacy blueprint structure to the new application structure, minimizing risk and ensuring continued functionality throughout the process.

The end result will be a cleaner, more maintainable codebase that follows Flask best practices and provides a solid foundation for future development.
