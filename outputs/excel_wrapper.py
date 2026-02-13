from pathlib import Path
import logging
from typing import Optional
from .excel import ExcelOutput


class SingleExcelWriter:
    _instance: Optional[ExcelOutput] = None

    @classmethod
    def init(cls, output_dir: str = 'RSA_OneDrive') -> None:
        cls._instance = ExcelOutput(output_dir=output_dir)
        logging.info('Initialized SingleExcelWriter with dir: %s', output_dir)

    @classmethod
    def get_wrapper(cls) -> ExcelOutput:
        if cls._instance is None:
            raise RuntimeError('Run the init method of this class first')
        return cls._instance

