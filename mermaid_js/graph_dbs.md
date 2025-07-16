mindmap
  root((Graph Databases in Cloud))

    AWS
      Neptune
        Supports Gremlin
        Supports SPARQL
        RDF & Property Graphs
        Fully Managed
        IAM & VPC Integration
        Good for Knowledge Graphs

    GCP
      No Native Graph DB
      Third-party Options
        Neo4j Aura
        DataStax Astra DB
      Analytics Workarounds
        BigQuery + GraphFrames
      Not Ideal for OLTP

    Azure
      Cosmos DB
        Gremlin API Support
        Multi-model (doc, key-value, graph)
        Global Distribution
        Tight MS Integration
        Lacks Deep Graph Features

    Considerations
      Use Case Driven
        OLTP -> Neptune / Cosmos
        Analytics -> BigQuery
        Deep Graph -> Neo4j
      Language Support
        Gremlin
        SPARQL
      Ecosystem Fit
        AWS = Deep integration
        Azure = Multi-model
        GCP = Flexible via partners
