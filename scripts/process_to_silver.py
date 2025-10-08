#!/usr/bin/env python3
"""
Unified Bronze-to-Silver processing script.
Automatically dispatches to appropriate pipeline based on source type.
"""

import argparse
from pathlib import Path


from modules.base_script import BaseScript, register_script
from modules.data_io import ensure_data_directories, log
from modules.pipeline.domain_pipelines import (
    AmeldingProcessingPipeline,
    LegalTextProcessingPipeline,
    RatesProcessingPipeline,
    SaftProcessingPipeline,
)
from modules.pipeline.processing_pipeline import ProcessingPipeline


@register_script("process-to-silver")
class ProcessToSilverScript(BaseScript):
    """Unified script to process all Bronze data to Silver layer."""

    def __init__(self):
        super().__init__(
            "process_to_silver",
            "Process Bronze layer data to Silver layer (all types)",
        )

    def _configure_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Configure command-line arguments."""
        parser.add_argument(
            "--type",
            choices=["legal", "rates", "amelding", "saft", "all"],
            default="all",
            help="Type of data to process (default: all)",
        )
        parser.add_argument(
            "--domain",
            help="Filter by domain (tax, accounting, reporting)",
        )

    def _execute(self) -> int:
        """Execute the Bronze to Silver processing."""
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data"
        sources_file = project_root / "configs" / "sources.csv"

        directories = ensure_data_directories(data_dir)
        bronze_dir = directories["bronze"]
        silver_dir = directories["silver"]

        data_type = self.args.type
        domain_filter = self.args.domain

        pipelines_to_run: list[tuple[str, ProcessingPipeline]] = []

        if data_type in ["legal", "all"]:
            pipelines_to_run.append(("Legal Texts", LegalTextProcessingPipeline()))

        if data_type in ["rates", "all"]:
            pipelines_to_run.append(("VAT Rates", RatesProcessingPipeline()))

        if data_type in ["amelding", "all"]:
            pipelines_to_run.append(("A-meldingen", AmeldingProcessingPipeline()))

        if data_type in ["saft", "all"]:
            pipelines_to_run.append(("SAF-T", SaftProcessingPipeline()))

        if not pipelines_to_run:
            log.error(f"Invalid data type: {data_type}")
            return 1

        log.info(f"Processing {len(pipelines_to_run)} data type(s) to Silver layer")

        total_processed = 0
        total_failed = 0
        all_errors = []

        for pipeline_name, pipeline in pipelines_to_run:
            log.info(f"\n{'=' * 60}")
            log.info(f"Processing {pipeline_name}")
            log.info(f"{'=' * 60}")

            try:
                pipeline.setup(sources_file, bronze_dir, silver_dir)

                if domain_filter and hasattr(pipeline, "source_loader"):
                    log.info(f"Filtering by domain: {domain_filter}")

                result = pipeline.execute()

                total_processed += result.processed_items
                total_failed += result.failed_items
                all_errors.extend(result.errors)

            except Exception as e:
                error_msg = f"Failed to process {pipeline_name}: {str(e)}"
                log.error(error_msg)
                all_errors.append(error_msg)
                total_failed += 1

        log.info(f"\n{'=' * 60}")
        log.info("OVERALL SUMMARY")
        log.info(f"{'=' * 60}")
        log.info(f"Pipelines run: {len(pipelines_to_run)}")
        log.info(f"Total processed: {total_processed}")
        log.info(f"Total failed: {total_failed}")

        if all_errors:
            log.error(f"\nTotal errors: {len(all_errors)}")
            for error in all_errors[:10]:
                log.error(f"  • {error}")
            if len(all_errors) > 10:
                log.error(f"  ... and {len(all_errors) - 10} more errors")

        log.info(f"{'=' * 60}")

        return 0 if total_failed == 0 else 1


def main():
    """Main entry point."""
    script = ProcessToSilverScript()
    return script.main()


if __name__ == "__main__":
    main()
