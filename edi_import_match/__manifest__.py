{
    "name": "EDI Import Match",
    "version": "12.0.1.0.0",
    "category": "Tools",
    "summary": "Try to avoid duplicate before importing",
    "author": "SHS-AV s.r.l.",
    "website": "https://www.zeroincombenze.it/crm",
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": ["base_import"],
    "data": [
        "security/ir.model.access.csv",
        "data/edi_import_match.xml",
        "views/edi_import_match_view.xml",
    ],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
    "application": False,
}
