"""
Base pipeline component for common pipeline patterns.
Provides shared functionality for all pipeline types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..data_io import ensure_data_directories, log


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    
    success: bool
    total_items: int
    processed_items: int
    failed_items: int
    errors: List[str]
    execution_time: float
    metadata: Dict[str, Any]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        self.failed_items += 1
    
    def add_processed(self, count: int = 1) -> None:
        """Add processed items to the result."""
        self.processed_items += count


class BasePipeline(ABC):
    """Base class for all pipeline components."""
    
    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.start_time: Optional[datetime] = None
        self.result: Optional[PipelineResult] = None
    
    def setup_paths(self, project_root: Optional[Path] = None) -> Dict[str, Path]:
        """Setup common paths for the pipeline."""
        if project_root is None:
            # Default to parent of scripts directory
            project_root = Path(__file__).parent.parent.parent
        
        paths = {
            "project_root": project_root,
            "data_dir": project_root / "data",
            "bronze_dir": project_root / "data" / "bronze",
            "silver_dir": project_root / "data" / "silver",
            "gold_dir": project_root / "data" / "gold",
            "sources_file": project_root / "configs" / "sources.csv",
        }
        
        # Ensure directories exist
        ensure_data_directories(paths["data_dir"])
        
        return paths
    
    def start_execution(self) -> None:
        """Start pipeline execution."""
        self.start_time = datetime.now()
        self.result = PipelineResult(
            success=False,
            total_items=0,
            processed_items=0,
            failed_items=0,
            errors=[],
            execution_time=0.0,
            metadata={}
        )
        log.info(f"Starting {self.pipeline_name} pipeline")
    
    def finish_execution(self) -> PipelineResult:
        """Finish pipeline execution and return result."""
        if self.start_time and self.result:
            self.result.execution_time = (datetime.now() - self.start_time).total_seconds()
            self.result.success = self.result.failed_items == 0
            
            duration = self.result.execution_time
            log.info(f"Completed {self.pipeline_name} pipeline in {duration:.2f}s")
            log.info(f"Success rate: {self.result.success_rate:.1f}% ({self.result.processed_items}/{self.result.total_items})")
            
            if self.result.errors:
                log.warning(f"Pipeline had {len(self.result.errors)} errors")
        
        return self.result
    
    def print_summary(self, title: str, item_name: str) -> None:
        """Print a standardized summary."""
        if not self.result:
            return
            
        print("\n" + "=" * 50)
        print(title.upper())
        print("=" * 50)
        print(f"Total {item_name}: {self.result.total_items}")
        print(f"Processed {item_name}: {self.result.processed_items}")
        print(f"Failed {item_name}: {self.result.failed_items}")
        print(f"Success rate: {self.result.success_rate:.1f}%")
        print(f"Execution time: {self.result.execution_time:.2f}s")
        
        if self.result.errors:
            print(f"\nErrors ({len(self.result.errors)}):")
            for error in self.result.errors:
                print(f"  • {error}")
        
        print("=" * 50)
    
    @abstractmethod
    def execute(self) -> PipelineResult:
        """Execute the pipeline."""
        pass
    
    def run(self) -> int:
        """Run the pipeline and return exit code."""
        try:
            self.start_execution()
            result = self.execute()
            self.finish_execution()
            return 0 if result.success else 1
        except Exception as e:
            log.error(f"Pipeline {self.pipeline_name} failed: {e}", exc_info=True)
            return 1
