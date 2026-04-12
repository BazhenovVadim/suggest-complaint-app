package ru.it.solutions.suggest.complaint.app.model.mappers;

import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;
import ru.it.solutions.suggest.complaint.app.model.dto.UserResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.RegisterRequest;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;

@Mapper(componentModel = "spring")
public interface UserMapper {
    @Mapping(target = "id", ignore = true)
    UserEntity toEntity(RegisterRequest createDto);

    UserResponseDto toResponseDto(UserEntity user);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(@MappingTarget UserEntity target, UserResponseDto source);
}
