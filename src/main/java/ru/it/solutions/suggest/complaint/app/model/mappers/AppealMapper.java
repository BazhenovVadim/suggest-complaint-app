package ru.it.solutions.suggest.complaint.app.model.mappers;

import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring")
public interface AppealMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "user", ignore = true)
    @Mapping(target = "appealNumber", ignore = true)
    Appeal toEntity(AppealCreateDto createDto);

    AppealResponseDto toResponseDto(Appeal appeal);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "user", ignore = true)
    @Mapping(target = "appealNumber", ignore = true)
    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(@MappingTarget Appeal target, AppealUpdateDto source);
}