import logging
from .models import Template, Tag

logger = logging.getLogger('workstation_coordinator')

class TemplateHandler:
    def __init__(self) -> None:
        pass

    def get_all(self) -> list:
        return list(Template.objects.all())
    
    def get_tags_containing_string_anycase(self, tag_string: str) -> list[Tag]:
        return list(Tag.objects.filter(name__icontains=tag_string))
    
    def get_all_tags(self) -> list[Tag]:
        return list(Tag.objects.all())
    
    def get_tags_by_string(self, input_tags: list[str]) -> list[Tag]:
        logger.info(f'Processing input tag list: {input_tags}')
        tags = [] 
        for tag in input_tags:
            tag = Tag.objects.filter(name=tag).first()
            tags.append(tag)
        return tags
    
    def get_tags_compatible_with_tags(self, input_tags: list[Tag]) -> list[Tag]:
        all_templates = Template.objects.all()
        compatible_tags: set = set()

        for template in all_templates:
            template_tags = template.tags.all()
            if all([tag in template_tags for tag in input_tags]):
                for tag in template_tags:
                    if tag not in input_tags:
                        compatible_tags.add(tag) 

        return list(compatible_tags)
    
    def get_tag_names(self, tags: list[Tag]) -> list[str]:
        return [tag.name for tag in tags]
