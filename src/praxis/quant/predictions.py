from datetime import datetime, timezone
from praxis.core.quant_models import Prediction, PredictionAssessment, Quantity
class PredictionTracker:
    @staticmethod
    def observe(p:Prediction,actual:Quantity)->tuple[Prediction,PredictionAssessment]:
        if actual.unit!=p.predicted.unit or actual.dimension!=p.predicted.dimension: raise ValueError('actual and predicted units/dimensions must match')
        p.actual=actual; p.observed_at=datetime.now(timezone.utc); err=actual.value-p.predicted.value
        pe=(err/p.predicted.value*100) if p.predicted.value else None
        direction='on_target' if err==0 else ('above' if err>0 else 'below')
        return p,PredictionAssessment(prediction_id=p.id,absolute_error=abs(err),percentage_error=abs(pe) if pe is not None else None,direction=direction)
