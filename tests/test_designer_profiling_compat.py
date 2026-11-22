"""Run the real isolated Designer 0.10 profiler, without generation or network."""
import os
from pathlib import Path
import subprocess
import textwrap


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / 'integrations/designer/.venv/bin/python'


def isolated(source, folder):
    assert PYTHON.is_file(), 'Install the pinned Designer integration before validating its compatibility boundary'
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONPATH': os.pathsep.join([str(ROOT / 'integrations/designer'), str(ROOT / 'src')])}
    completed = subprocess.run([str(PYTHON), '-c', textwrap.dedent(source), str(folder)],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=40)
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_native_single_row_and_multi_row_reports_preserve_data_and_undefined_statistics(tmp_path):
    isolated('''
        from pathlib import Path
        import hashlib,json,math,sys
        from types import SimpleNamespace
        import pandas as pd
        import data_designer.config as dd
        from data_designer.engine.analysis.dataset_profiler import DataDesignerDatasetProfiler,DatasetProfilerConfig
        from data_designer.engine.analysis.utils import column_statistics_calculations as calculations
        from learning_preferences import capture_profiling
        from profiling_compat import native_missing_token_statistics
        out=Path(sys.argv[1])
        columns=[dd.SeedDatasetColumnConfig(name='original_profile_json'),
            dd.SeedDatasetColumnConfig(name='original_profile_sha256'),
            dd.LLMStructuredColumnConfig(name='retail_situation',model_alias='offline',
                prompt='Read {{ original_profile_json }}',output_format={'type':'object'})]
        profiler=DataDesignerDatasetProfiler(DatasetProfilerConfig(column_configs=columns),
            SimpleNamespace(run_config=dd.RunConfig()))
        frame=pd.DataFrame({'original_profile_json':['{"interests":"retail"}'],
            'original_profile_sha256':['synthetic-source-hash'],
            'retail_situation':[{'goal':'retail analysis'}]})
        seed=out/'seed.jsonl';seed.write_text(frame.iloc[:1].to_json(orient='records'))
        batch=out/'batch.parquet';frame.to_parquet(batch)
        hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [seed,batch]}
        original=calculations.calculate_output_token_stats
        try:
            profiler.profile_dataset(1,frame)
        except TypeError as exc:
            assert 'NAType' in str(exc)
        else:
            raise AssertionError('The pinned native failure did not reproduce; revalidate the shim')
        with native_missing_token_statistics() as receipt:
            report=profiler.profile_dataset(1,pd.read_parquet(batch))
        assert calculations.calculate_output_token_stats is original
        serialized=json.loads(report.model_dump_json())
        generated=next(row for row in serialized['column_statistics'] if row['column_name']=='retail_situation')
        assert generated['output_tokens_stddev'] is None
        assert generated['output_tokens_mean']>0 and generated['num_records']==1
        assert receipt['normalized_fields']==[{'column':'retail_situation','statistic':'output_tokens_stddev'}]
        assert report.num_records==report.target_num_records==1 and len(report.column_statistics)==3
        capture_profiling(out,result=SimpleNamespace(load_analysis=lambda:report),batches=[batch],compatibility=receipt)
        saved=json.loads((out/'designer-analysis.json').read_text(),
            parse_constant=lambda value:(_ for _ in ()).throw(AssertionError(value)))
        assert saved==serialized
        status=json.loads((out/'designer-profiling.json').read_text())
        assert status['status']=='completed' and status['analysis_report']=='designer-analysis.json'
        assert status['compatibility']['generation_replayed'] is False
        assert all(hashlib.sha256(p.read_bytes()).hexdigest()==value for p,value in hashes.items())
        double=pd.concat([frame,frame.assign(retail_situation=[{'goal':'a much longer practice task for sales and inventory'}])],ignore_index=True)
        before=profiler.profile_dataset(2,double).model_dump_json()
        with native_missing_token_statistics() as multi:
            after=profiler.profile_dataset(2,double).model_dump_json()
        assert before==after and multi['normalized_fields']==[]
        # The native missing/nonfinite JSON representation remains null, never zero.
        model=report.column_statistics[-1].model_copy(update={'output_tokens_stddev':math.nan})
        assert json.loads(model.model_dump_json())['output_tokens_stddev'] is None
        try:
            with native_missing_token_statistics():
                raise RuntimeError('offline forced failure')
        except RuntimeError:
            pass
        assert calculations.calculate_output_token_stats is original
    ''', tmp_path)


def test_retail_profiling_error_stops_without_salvaging_a_generated_row(tmp_path):
    isolated('''
        from pathlib import Path
        import json,os,sys
        from types import SimpleNamespace
        import data_designer.config as dd
        from data_designer.interface.errors import DataDesignerProfilingError
        import retail_situation
        out=Path(sys.argv[1])
        request=out/'request.json'
        request.write_text(json.dumps({'original_profile_json':'{"interests":"retail"}',
            'original_profile_sha256':'synthetic-hash','schema':{'type':'object'}}))
        os.environ.update(LAB_DESIGNER_MODEL='offline-only',LAB_DESIGNER_GATEWAY_URL='http://offline.invalid/v1',
            LAB_DESIGNER_GATEWAY_KEY='offline-not-a-credential')
        class Designer:
            run_config=dd.RunConfig()
            model_provider_registry=SimpleNamespace(model_dump=lambda **kwargs:{})
            def __init__(self,**kwargs):pass
            def set_run_config(self,value):self.run_config=value
            def validate(self,builder):pass
            def create(self,*args,**kwargs):
                raise DataDesignerProfilingError('Different native profiling failure')
        retail_situation.DataDesigner=Designer
        try:retail_situation.generate(request,out/'result.json')
        except DataDesignerProfilingError as exc:assert 'Different native' in str(exc)
        else:raise AssertionError('A profiling error was incorrectly accepted')
        receipt=json.loads((out/'designer-profiling.json').read_text())
        assert receipt['status']=='failed' and receipt['analysis_report'] is None
        assert not (out/'result.json').exists() and not (out/'designer-analysis.json').exists()
    ''', tmp_path)
