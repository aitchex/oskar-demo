# Oskar Demo

Website: [oskarfishing.com](https://oskarfishing.com/)

## Important Files

```py
.
├─ account/
│  ├─ forms.py         # User creation and update forms
│  ├─ models.py        # User and Address models
│  └─ views.py         # Login, Profile, etc.
├─ shop/
│  ├─ models.py        # Product and Variation models
│  └─ views.py         # Home, Shop and Product pages
├─ templates/
│  ├─ shop/
│  │  ├─ product.html  # Product template
│  │  └─ shop.html     # Shop template
│  └─ base.html        # Django base template
├─ utils/
│  ├─ const.py         # Constant variables
│  ├─ decorator.py     # Cache related decorators
│  └─ model.py         # Thumbnail generation
└─ ...
```
