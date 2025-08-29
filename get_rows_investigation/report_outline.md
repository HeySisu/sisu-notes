# title

# executive summary

# action item 1: add logging

link to the logging pr
datadog dashboard

# action item 2: fix database connection issue

problem:
- datadog link to show the connection issue, group by task names. screenshot as well
- aws rds proxy ocnfiguration screenshots

proposed solution
protential impact

known issues:
- the connection state is NULL is not a zombie connection. we use aws rds proxy to connect to the database, and it is natually we cannot get the state.
this is NOT a zombie connection.

# action item 3: add index to cell table

action:
add these following indexes:
sql 1
sql 2
sql 3

problem 1:
code snippet with link
solution: add index: x, y, z

problem 2:
code snippet with link
solution: xxx

potential impact:

# action item 4: other database fixes

problem:
-- database sql query and results
-- code snippets

proposed solution
potential impact

# Appendix

database overview, critical tables, sizes, etc

cell table existing indexes



# references

* datadog query to show the connection time issue:
- apm trace: env:prod resource_name:postgres.connect @duration:>1000000000
- link: https://app.datadoghq.com/apm/traces?query=env%3Aprod%20resource_name%3Apostgres.connect%20%40duration%3A%3E1000000000&agg_m=count&agg_m_source=base&agg_t=count&cols=core_service%2Ccore_resource_name%2Clog_duration%2Clog_http.method%2Clog_http.status_code&fromUser=false&graphType=waterfall&historicalData=true&messageDisplay=inline&query_translation_version=v0&shouldShowLegend=true&sort=time&sort_by=%40duration&sort_order=desc&spanID=15735952627381790826&spanType=all&storage=hot&trace_group_by_from=a&trace_group_by_metrics=a&traceQuery=&view=spans&viz=stream&start=1756411636680&end=1756426036680&paused=false

* datadog query for long hydration time:
- log: run_get_rows_db_queries performance env:prod @hydration_time:>2.0
- sql query: