

def fitModHtml(mod):
    if mod != None:
        return "<a href=\"#\" rel=\"tooltip\" data-placement=\"top\" title=\"\" data-original-title=\"%s\"><img class=\"img-rounded\" src=\"https://image.eveonline.com/Type/%d_32.png\" width=\"32\" height=\"32\" alt=\"%s\"></a>" % (mod.InvType.typeName, mod.InvType.typeID, mod.InvType.typeName)
    else:
        return ""
