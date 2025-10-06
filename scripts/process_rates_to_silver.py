#!/usr/bin/env python3
"""
Refactored VAT rates processing script using pipeline architecture.
Demonstrates the new pipeline pattern.
"""

from pathlib import Path

from modules.base_script import BaseScript, register_script
from modules.pipeline.domain_pipelines import RatesProcessingPipeline


@register_script("process-rates-to-silver")
class ProcessRatesToSilverScript(BaseScript):
    """Script to process VAT rates using pipeline architecture."""
    
    def __init__(self):
        super().__init__("process_rates_to_silver")
    
    def _execute(self) -> int:
        """Execute the VAT rates processing using pipeline."""
        # Setup paths
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        bronze_dir = project_root / "data" / "bronze"
        silver_dir = project_root / "data" / "silver"
        sources_file = project_root / "configs" / "sources.csv"
        
        # Create and setup pipeline
        pipeline = RatesProcessingPipeline()
        pipeline.setup(sources_file, bronze_dir, silver_dir)
        
        # Run pipeline
        result = pipeline.run()
        
        # Print summary
        pipeline.print_summary("VAT RATES PROCESSING", "rates")
        
        return result


def main():
    """Main entry point."""
    script = ProcessRatesToSilverScript()
    return script.main()


if __name__ == "__main__":
    main()
