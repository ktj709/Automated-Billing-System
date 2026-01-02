import json

from config import Config


# Import neo4j only if available (optional dependency)
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    GraphDatabase = None
    HAS_NEO4J = False


class GraphService:

    def save_tariff_rule(self, tariff_type, rule_data):
        with self.driver.session() as session:
            session.run(
                "MERGE (t:TariffRule {type: $tariff_type}) SET t.data = $rule_data",
                tariff_type=tariff_type,
                rule_data=json.dumps(rule_data)
            )

    def get_tariff_rule(self, tariff_type):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (t:TariffRule {type: $tariff_type}) RETURN t.data AS data",
                tariff_type=tariff_type
            )
            record = result.single()
            if record and record["data"]:
                return json.loads(record["data"])
            return None
    def __init__(self, uri: str | None = None, auth: tuple[str, str] | None = None):
        self.connection_error = None

        if not HAS_NEO4J:
            self.driver = None
            self.connection_error = "Neo4j driver not installed"
            return

        resolved_uri = uri or getattr(Config, "NEO4J_URI", "")

        if auth is None:
            resolved_user = getattr(Config, "NEO4J_USER", "")
            resolved_password = getattr(Config, "NEO4J_PASSWORD", "")
            resolved_auth = (resolved_user, resolved_password)
        else:
            resolved_auth = auth

        if not resolved_uri:
            self.driver = None
            self.connection_error = "NEO4J_URI not configured"
            return

        if not resolved_auth[0] or not resolved_auth[1]:
            self.driver = None
            self.connection_error = "NEO4J_USER/NEO4J_PASSWORD not configured"
            return

        try:
            self.driver = GraphDatabase.driver(resolved_uri, auth=resolved_auth)
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            self.driver = None
            self.connection_error = str(e)

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def get_readings_for_customer(self, customer_id):
        query = (
            "MATCH (c:Customer {id: $customer_id})-[:OWNS]->(m:Meter)-[:HAS_READING]->(r:Reading) "
            "RETURN r.id AS reading_id, r.value AS reading_value, r.date AS reading_date, m.id AS meter_id"
        )
        with self.driver.session() as session:
            result = session.run(query, customer_id=customer_id)
            return [record.data() for record in result]

    def upsert_bill(self, bill_data):
        import logging
        logger = logging.getLogger("graph_service")
        # Validate required fields
        required = ["customer_id", "meter_id", "billing_period_start", "billing_period_end", "amount"]
        for key in required:
            if key not in bill_data or bill_data[key] is None:
                logger.error(f"Missing required bill field: {key} in bill_data: {bill_data}")
                raise ValueError(f"Missing required bill field: {key}")
        # Use Supabase bill 'id' as unique identifier
        bill_id = str(bill_data.get('id', ''))
        logger.info(f"Upserting bill to Neo4j: bill_id={bill_id}, bill_data={bill_data}")
        try:
            with self.driver.session() as session:
                session.run("MERGE (c:Customer {id: $customer_id})", customer_id=bill_data["customer_id"])
                session.run("MERGE (m:Meter {id: $meter_id})", meter_id=bill_data["meter_id"])
                session.run(
                    "MERGE (b:Bill {id: $bill_id}) SET b = $props",
                    bill_id=bill_id,
                    props={
                        "id": bill_id,
                        "amount": bill_data["amount"],
                        "start": bill_data["billing_period_start"],
                        "end": bill_data["billing_period_end"],
                        "customer_id": bill_data["customer_id"],
                        "meter_id": bill_data["meter_id"],
                        "status": bill_data.get("status", ""),
                        "payment_link": bill_data.get("payment_link", ""),
                        "consumption_kwh": bill_data.get("consumption_kwh", 0)
                    }
                )
                session.run("MATCH (c:Customer {id: $customer_id}), (b:Bill {id: $bill_id}) MERGE (b)-[:FOR]->(c)", customer_id=bill_data["customer_id"], bill_id=bill_id)
                session.run("MATCH (m:Meter {id: $meter_id}), (b:Bill {id: $bill_id}) MERGE (b)-[:FOR_METER]->(m)", meter_id=bill_data["meter_id"], bill_id=bill_id)
            logger.info(f"Bill upserted successfully: bill_id={bill_id}")
        except Exception as e:
            logger.error(f"Neo4j upsert error for bill_id={bill_id}: {e}")
            raise

    def get_all_bills(self):
        with self.driver.session() as session:
            query = """
            MATCH (b:Bill)-[:FOR]->(c:Customer), (b)-[:FOR_METER]->(m:Meter)
            RETURN b, c, m
            """
            result = session.run(query)
            bills = []
            for record in result:
                b = record["b"]
                c = record["c"]
                m = record["m"]
                bills.append({
                    "id": b.get("id"),
                    "customer_id": b.get("customer_id"),
                    "meter_id": b.get("meter_id"),
                    "billing_period_start": b.get("start"),
                    "billing_period_end": b.get("end"),
                    "consumption_kwh": b.get("consumption_kwh", 0),
                    "amount": b.get("amount"),
                    "status": b.get("status", ""),
                    "payment_link": b.get("payment_link", ""),
                })
            return bills

    def advanced_bill_query(self, cypher_query):
        with self.driver.session() as session:
            return session.run(cypher_query)

    def rag_query(self, question, openai_api_key):
        import openai
        openai.api_key = openai_api_key
        # Retrieve context from Neo4j
        with self.driver.session() as session:
            context_query = "MATCH (b:Bill)-[:FOR]->(c:Customer), (b)-[:FOR_METER]->(m:Meter) RETURN b, c, m LIMIT 5"
            result = session.run(context_query)
            context = ""
            for record in result:
                b = record["b"]
                c = record["c"]
                m = record["m"]
                context += f"Bill: {b.get('amount')} for {c.get('id')} on meter {m.get('id')} from {b.get('start')} to {b.get('end')}\n"
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()

if __name__ == "__main__":
    graph = GraphService()
    readings = graph.get_readings_for_customer("CUST001")
    for r in readings:
        print(r)
    graph.close()
