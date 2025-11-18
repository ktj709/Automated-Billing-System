// Neo4j Cypher queries for graph database setup

// Create Customer nodes
CREATE (c:Customer {
    id: 'CUST001',
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+1234567890',
    created_at: datetime()
});

// Create Meter nodes
CREATE (m:Meter {
    id: 'METER001',
    type: 'smart_meter',
    location: '123 Main St',
    installed_date: date('2025-01-01')
});

// Create Tariff nodes with tiered pricing
CREATE (t:Tariff {
    id: 'TARIFF001',
    name: 'Residential Standard',
    active: true,
    tiers: [
        {tier: 'Tier 1', min: 0, max: 100, rate: 0.10},
        {tier: 'Tier 2', min: 101, max: 300, rate: 0.12},
        {tier: 'Tier 3', min: 301, max: 999999, rate: 0.15}
    ],
    fixed_charge: 5.00,
    tax_rate: 0.10
});

// Create relationships
MATCH (c:Customer {id: 'CUST001'}), (m:Meter {id: 'METER001'})
CREATE (c)-[:OWNS_METER]->(m);

MATCH (m:Meter {id: 'METER001'}), (t:Tariff {id: 'TARIFF001'})
CREATE (m)-[:USES_TARIFF]->(t);

// Query to get all active tariffs
// MATCH (t:Tariff) WHERE t.active = true RETURN t;

// Query to get customer's meters with tariffs
// MATCH (c:Customer {id: 'CUST001'})-[:OWNS_METER]->(m:Meter)-[:USES_TARIFF]->(t:Tariff)
// RETURN c, m, t;

// Query to get billing history
// MATCH (c:Customer {id: 'CUST001'})-[:HAS_BILL]->(b:Bill)
// RETURN b
// ORDER BY b.date DESC
// LIMIT 12;
