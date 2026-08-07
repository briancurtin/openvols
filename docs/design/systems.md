# Systems design

The OpenVols system is comprised of several systems

## Frontend

Users do all of their interaction in the browser

## API

A REST API service communciates with the UI to support user interaction

## Notifications

A scheduled service runs periodically to send participation reminder notifications

## Observability collector

The systems emit OTel data, which is collected and sent to an observability platform

# Overview

```mermaid
architecture-beta

    group saas(cloud)[Hosted SaaS Services]
        service postgres(database)[Postgres] in saas
        service observability(database)[Observability] in saas

    group openvols(cloud)[OpenVols Platform]
        service frontend(internet)[UI] in openvols
        service loadbalancer(server)[Load Balancer] in openvols
        service api_node0(server)[API] in openvols
        service api_node1(server)[API] in openvols
        service collector(server)[OTel Collector] in openvols
        service scheduler(server)[Scheduler] in openvols
        service notifications(server)[Notifications] in openvols

    frontend:B <--> T:loadbalancer
    align column frontend loadbalancer

    align row scheduler loadbalancer

    scheduler:B --> T:notifications
    align column scheduler notifications

    loadbalancer:B --> T:api_node0
    loadbalancer:B --> T:api_node1
    align row api_node0 api_node1
    align column api_node0 collector

    api_node0:B --> T:collector
    api_node1:B --> T:collector
    notifications:B --> T:collector
    collector:B --> T: observability
    align column collector observability

    postgres:T <--> B:notifications
    postgres:T <--> B:api_node0
    postgres:T <--> B:api_node1
```
