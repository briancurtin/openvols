"""
OTel metrics and tracing setup

The OTLPSpanExporter supports both HTTP and gRPC. This implementation currently
uses gRPC, mostly based on it seeming the common choice.
"""

import os
import sys

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

# Use the process name as our resource, so entrypoints are tracked uniquely
resource = Resource.create(attributes={SERVICE_NAME: os.path.basename(sys.argv[0])})

tracer_provider = TracerProvider(resource=resource)

# In a deployed environment we should be using a real exporter
# In development, use in-memory console exporters
if endpoint := os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
    reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
else:
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    reader = PeriodicExportingMetricReader(ConsoleMetricExporter())

tracer_provider.add_span_processor(processor)
trace.set_tracer_provider(tracer_provider)

meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
