# AI Model Placement

Place your trained TensorFlow / Keras model file in this directory.

## Expected path (default)

```
ai/ml/model.keras
```

Or `.h5` format:

```
ai/ml/model.h5
```

## Overriding the path

Set `ML_MODEL_PATH` in your `.env` file to an absolute or relative path:

```env
ML_MODEL_PATH=/opt/models/eurosat_resnet50.keras
```

## Class labels

The default class list matches the **EuroSAT** benchmark (10 classes):

```env
ML_CLASS_NAMES=AnnualCrop,Forest,HerbaceousVegetation,Highway,Industrial,Pasture,PermanentCrop,Residential,River,SeaLake
```

Update `ML_CLASS_NAMES` to match the order of your model's output neurons exactly.

## Image size

Default resize target is 64×64 px (EuroSAT standard):

```env
# Defined in settings/base.py — change if your model uses a different input size
ML_IMAGE_SIZE = (64, 64)
```

## Testing

```bash
python manage.py test_ai_pipeline --image path/to/sample.jpg
```
