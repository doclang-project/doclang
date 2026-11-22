#ifndef DOCLANG_NATIVE_DCLG_NODE_CAPTION_H_
#define DOCLANG_NATIVE_DCLG_NODE_CAPTION_H_

#include <string>
#include <string_view>

#include <doclang/dclg_node.h>

namespace doclang::native
{
  inline void set_element_caption(pugi::xml_node element, std::string_view text)
  {
    auto caption = element.child(xml_name(element_tag::caption));
    if(not caption)
      {
        pugi::xml_node anchor;
        for(auto child : element.children())
          {
            const std::string_view name = child.name();
            if(name == "label" or name == "thread" or name == "xref" or name == "href"
               or name == "layer" or name == "location")
              {
                continue;
              }
            anchor = child;
            break;
          }
        caption = anchor ? element.insert_child_before(xml_name(element_tag::caption), anchor)
                         : element.append_child(xml_name(element_tag::caption));
      }
    caption.remove_children();
    caption.append_child(pugi::node_pcdata).set_value(std::string(text).c_str());
  }
}

#endif
